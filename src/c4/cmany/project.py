#!/usr/bin/env python3

import os
import glob
import json
import copy
from collections import OrderedDict as odict

from . import util
from . import conf

from .build_flags import BuildFlags
from .build_type import BuildType
from .system import System
from .architecture import Architecture
from .compiler import Compiler
from .variant import Variant
from .build import Build

from .cmake import getcachevars


# -----------------------------------------------------------------------------
class Project:

    def __init__(self, **kwargs):

        self.kwargs = kwargs

        proj_dir = kwargs.get('proj_dir', os.getcwd())
        proj_dir = os.getcwd() if proj_dir == "." else proj_dir
        if not os.path.isabs(proj_dir):
            proj_dir = os.path.abspath(proj_dir)
        self.root_dir = proj_dir

        def _getdir(attr_name, default):
            d = kwargs.get(attr_name)
            if d is None:
                d = os.path.join(os.getcwd(), default)
            else:
                if not os.path.isabs(d):
                    d = os.path.join(os.getcwd(), d)
            return d
        self.build_dir = _getdir('build_dir', 'build')
        self.install_dir = _getdir('install_dir', 'install')

        self.cmakelists = util.chkf(self.root_dir, "CMakeLists.txt")
        self.num_jobs = kwargs.get('jobs')
        self.targets = kwargs.get('target')

        self.load_configs()

        vars = kwargs.get('variants')
        if not vars:
            vars = ['none']

        _get = lambda n,c: __class__._getarglist(n, c, **kwargs)
        self.systems = _get('systems', System)
        self.architectures = _get('architectures', Architecture)
        self.buildtypes = _get('build_types', BuildType)
        self.compilers = _get('compilers', Compiler)
        self.variants = Variant.create(vars)

        self.builds = []
        for s in self.systems:
            for a in self.architectures:
                for c in self.compilers:
                    for m in self.buildtypes:
                        for v in self.variants:
                            self.add_build_if_valid(s, a, m, c, v)

        # add new build params as needed to deal with adjusted builds
        def _addnew(b, name):
            a = getattr(b, name)
            ali = getattr(self, name + 's')
            if not [elm for elm in ali if str(elm) == str(a)]:
                ali.append(a)
        for b in self.builds:
            if not b.adjusted:
                continue
            _addnew(b, 'system')
            _addnew(b, 'architecture')
            _addnew(b, 'buildtype')
            _addnew(b, 'compiler')
            _addnew(b, 'variant')

    @staticmethod
    def _getarglist(name, class_, **kwargs):
        g = kwargs.get(name)
        if g is None or not g:
            g = [class_.default()]
            return g
        l = []
        for i in g:
            l.append(class_(i))
        return l

    def load_configs(self):
        seq = [os.path.join(d, "cmany.yml") for d in (
            conf.CONF_DIR, conf.USER_DIR, self.root_dir)]
        if self.kwargs.get('no_default_config'):
            seq = []
        for f in self.kwargs['config_file']:
            if not os.path.isabs(f):
                f = os.path.join(self.root_dir, f)
            if not os.path.exists(f):
                raise Exception(f + ": does not exist")
            seq.append(f)
        self.configs = conf.Configs.load(seq)

    def add_build_if_valid(self, system, arch, buildtype, compiler, variant):
        if not self.is_valid(system, arch, buildtype, compiler, variant):
            return False

        # duplicate the build items, as they may be mutated due
        # to translation of their flags for the compiler
        def _dup_item(item):
            i = copy.deepcopy(item)
            i.flags.resolve_flag_aliases(compiler, aliases=self.configs.flag_aliases)
            return i
        s = _dup_item(system)
        a = _dup_item(arch)
        t = _dup_item(buildtype)
        c = _dup_item(compiler)
        v = _dup_item(variant)
        #
        f = BuildFlags('all_builds', compiler, aliases=self.configs.flag_aliases, **self.kwargs)
        f.resolve_flag_aliases(compiler, aliases=self.configs.flag_aliases)

        # create the build
        b = Build(self.root_dir, self.build_dir, self.install_dir,
                  s, a, t, c, v, f,
                  self.num_jobs, dict(self.kwargs))

        # When a build is created, its parameters may have been adjusted
        # because of an incompatible generator specification.
        # So drop this build if an equal one already exists
        if b.adjusted and self.exists(b):
            return False  # a similar build already exists

        # finally, this.
        self.builds.append(b)
        return True  # build successfully added

    def exists(self, build):
        for b in self.builds:
            if str(b.tag) == str(build.tag):
                return True
        return False

    def is_valid(self, sys, arch, mode, compiler, variant):
        # TODO
        return True

    def select(self, **kwargs):
        out = [b for b in self.builds]
        def _h(kw, attr):
            global out
            g = kwargs.get(kw)
            if g is not None:
                lo = []
                for b in out:
                    if str(getattr(b, attr)) == str(g):
                        lo.append(b)
                out = lo
        _h("sys", "system")
        _h("arch", "architecture")
        _h("compiler", "compiler")
        _h("buildtype", "buildtype")
        _h("variant", "variant")
        return out

    def create_tree(self, **restrict_to):
        builds = self.select(**restrict_to)
        for b in builds:
            b.create_dir()
            b.create_preload_file()
            # print(b, ":", d)

    def configure(self, **restrict_to):
        if not os.path.exists(self.build_dir):
            os.makedirs(self.build_dir)
        self._execute(Build.configure, "Configure", silent=False, **restrict_to)

    def build(self, **restrict_to):
        def do_build(build):
            build.build(self.targets)
        self._execute(do_build, "Build", silent=False, **restrict_to)

    def clean(self, **restrict_to):
        self._execute(Build.clean, "Clean", silent=False, **restrict_to)

    def install(self, **restrict_to):
        self._execute(Build.install, "Install", silent=False, **restrict_to)

    def run_cmd(self, cmd, **restrict_to):
        cmds = util.splitesc_quoted(cmd, ' ')
        def _run_cmd(b):
            with util.setcwd(b.builddir):
                util.runsyscmd(cmds)
        self._execute(_run_cmd, "Run cmd", silent=False, **restrict_to)

    def create_projfile(self):
        confs = []
        for b in self.builds:
            confs.append(b.json_data())
        jd = odict([('configurations', confs)])
        with open(self.configfile, 'w') as f:
            json.dump(jd, f, indent=2)

    def showvars(self, varlist):
        varv = odict()
        pat = os.path.join(self.build_dir, '*', 'CMakeCache.txt')
        g = glob.glob(pat)
        md = 0
        mv = 0
        for p in g:
            d = os.path.dirname(p)
            b = os.path.basename(d)
            md = max(md, len(b))
            vars = getcachevars(d, varlist)
            for k, v in vars.items():
                sk = str(k)
                if not varv.get(sk):
                    varv[sk] = odict()
                varv[sk][b] = v
                mv = max(mv, len(sk))
        #
        fmt = "{:" + str(mv) + "}[{:" + str(md) + "}]={}"
        for var, sysvalues in varv.items():
            for s, v in sysvalues.items():
                print(fmt.format(var, s, v))

    def showbuilds(self):
        for b in self.builds:
            print(b)

    def showbuilddirs(self):
        for b in self.builds:
            print(b.builddir)

    def showtargets(self):
        for t in self.builds[0].get_targets():
            print(t)

    def _execute(self, fn, msg, silent, **restrict_to):
        builds = self.select(**restrict_to)
        num = len(builds)
        if not silent:
            if num == 0:
                print("no builds selected")
        if num == 0:
            return
        if not silent:
            util.lognotice("")
            util.lognotice("===============================================")
            if num > 1:
                util.lognotice(msg + ": start", num, "builds:")
                for b in builds:
                    util.lognotice(b)
                util.lognotice("===============================================")
        for i, b in enumerate(builds):
            if not silent:
                if i > 0:
                    util.lognotice("\n")
                util.lognotice("-----------------------------------------------")
                if num > 1:
                    util.lognotice(msg + ": build #{} of {}:".format(i+1, num), b)
                else:
                    util.lognotice(msg, b)
                util.lognotice("-----------------------------------------------")
            fn(b)
            util.logdone(msg + ": finished build #{} of {}:".format(i + 1, num), b)
        if not silent:
            if num > 1:
                util.lognotice("-----------------------------------------------")
                util.logdone(msg + ": finished", num, "builds:")
                for b in builds:
                    util.logdone(b)
            util.lognotice("===============================================")
