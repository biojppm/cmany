#!/usr/bin/env python3

import os
import glob
import json
import copy
import re
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

        s, a, c, t, v = __class__.get_build_items(**kwargs)

        cr = CombinationRules(kwargs.get('combination_rules', []))
        combs = cr.valid_combinations(s, a, c, t, v)
        self.combination_rules = cr

        self.builds = []
        for s_, a_, c_, t_, v_ in combs:
            self.add_build(s_, a_, c_, t_, v_)

        self.systems = s
        self.architectures = a
        self.compilers = c
        self.buildtypes = t
        self.variants = v

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
    def get_build_items(**kwargs):
        _get = lambda name_, class_: __class__._get_build_item_arg(name_, class_, **kwargs)
        s = _get('systems', System)
        a = _get('architectures', Architecture)
        c = _get('compilers', Compiler)
        t = _get('build_types', BuildType)
        v = Variant.create(kwargs.get('variants'))
        return s, a, c, t, v

    @staticmethod
    def _get_build_item_arg(name, class_, **kwargs):
        g = kwargs.get(name)
        if g is None or not g:
            raise Exception("is this ever reached?")
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

    def add_build(self, system, arch, compiler, buildtype, variant):
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


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class CombinationPattern:

    def __init__(self, spec):
        self.rule = spec

    def matches(self, s, a, c, t, v):
        for i in (s, a, c, t, v):
            if re.search(self.rule, str(i)):
                # print("GOT A MATCH:", self.rule, i)
                return True
        s = Build.get_tag(s, a, c, t, v)
        print(s, type(s))
        if re.search(self.rule, s):
            # print("GOT A TAG MATCH:", self.rule, s)
            return True
        # print("NO MATCH:", self.rule, s)
        return False


# -----------------------------------------------------------------------------
class CombinationRule:
    """x=exclude / i=include"""

    def __init__(self, specs, x_or_i, any_or_all):
        assert x_or_i in ('x', 'i')
        assert any_or_all in ('any', 'all')
        self.patterns = []
        self.x_or_i = x_or_i
        self.any_or_all = 'y' if any_or_all == 'any' else 'l'
        for s in specs:
            cr = CombinationPattern(s)
            self.patterns.append(cr)

    def is_valid(self, s, a, c, t, v):
        result = True
        matches_all = True
        matches_none = True
        matches_any = False
        for pattern in self.patterns:
            if pattern.matches(s, a, c, t, v):
                matches_any = True
                matches_none = False
            else:
                matches_all = False
        if self.x_or_i == 'x':
            if matches_none:
                result = True
            else:
                if self.any_or_all == 'y':
                    result = not matches_any
                else:
                    result = not matches_all
        elif self.x_or_i == 'i':
            if matches_none:
                result = False
            else:
                if self.any_or_all == 'y':
                    result = matches_any
                else:
                    result = matches_all
        return result


# -----------------------------------------------------------------------------
class CombinationRules:

    def __init__(self, specs):
        self.rules = []
        for x_or_i, any_or_all, rules in specs:
            crc = CombinationRule(rules, x_or_i, any_or_all)
            self.rules.append(crc)

    def is_valid(self, s, a, c, t, v):
        result = 1
        for r in self.rules:
            result = r.is_valid(s, a, c, t, v)
        return result

    def valid_combinations(self, systems, archs, comps, types, variants):
        combs = []
        for s in systems:
            for a in archs:
                for c in comps:
                    for t in types:
                        for v in variants:
                            if not self.is_valid(s, a, c, t, v):
                                continue
                            combs.append((s, a, c, t, v))
        return combs
