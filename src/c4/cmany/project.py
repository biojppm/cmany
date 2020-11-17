#!/usr/bin/env python3

import os
import glob
import json
import copy
import timeit
from collections import OrderedDict as odict

from ruamel import yaml as yaml
from ruamel.yaml.comments import CommentedMap as CommentedMap

from . import util
from . import conf

from .build_flags import BuildFlags
from .build_item import BuildItem
from .build_type import BuildType
from .system import System
from .architecture import Architecture
from .compiler import Compiler
from .variant import Variant
from .build import Build

from .combination_rules import CombinationRules
from .cmake import getcachevars
from . import cmake
from . import err
from .util import path_exists as _pexists
from .util import logdbg as dbg


# -----------------------------------------------------------------------------
def _getdir(attr_name, default, kwargs, cwd):
    d = kwargs.get(attr_name)
    if d is None:
        d = os.path.join(cwd, default)
    else:
        if not os.path.isabs(d):
            d = os.path.join(cwd, d)
    d = util.abspath(d)
    return d


def _is_cmake_folder(folder):
    if folder is None:
        return False
    dbg("exists?", folder)
    if not _pexists(folder):
        dbg("does not exist:", folder)
        return None
    dbg("exists:", folder)
    if _pexists(folder, "CMakeLists.txt"):
        dbg("found CMakeLists.txt in", folder)
        return folder
    dbg("CMakeLists.txt not found in", folder)
    if _pexists(folder, "CMakeCache.txt"):
        dbg("found CMakeCache.txt in", folder)
        return folder
    dbg("CMakeCache.txt not found in", folder)
    return None


# -----------------------------------------------------------------------------
class Project:

    def __init__(self, **kwargs):
        #
        self.kwargs = kwargs
        self.num_jobs = kwargs.get('jobs')
        self.targets = kwargs.get('target')
        self.continue_on_fail = kwargs.get('continue')
        #
        cwd = util.abspath(os.getcwd())
        pdir = kwargs.get('proj_dir')
        dbg("cwd:", cwd)
        dbg("proj_dir:", pdir)
        if pdir == ".":
            pdir = cwd
        elif pdir is None:
            dbg("proj_dir not given")
            if pdir is None and self.targets:
                dbg("is the first target a cmake directory?", self.targets[0])
                pdir = _is_cmake_folder(self.targets[0])
                if pdir is not None:
                    self.targets = self.targets[1:]
            if pdir is None:
                dbg("picking current directory", cwd)
                pdir = cwd
        pdir = util.abspath(pdir)
        dbg("proj_dir, abs:", pdir)
        #
        if not _pexists(pdir):
            raise err.ProjDirNotFound(pdir)
        #
        self.cmakelists = os.path.join(pdir, "CMakeLists.txt")
        cmakecache = None
        if _pexists(self.cmakelists):
            dbg("found CMakeLists.txt:", self.cmakelists)
            self.build_dir = _getdir('build_dir', 'build', kwargs, cwd)
            self.install_dir = _getdir('install_dir', 'install', kwargs, cwd)
            self.root_dir = pdir
        elif _pexists(pdir, "CMakeCache.txt"):
            cmakecache = os.path.join(pdir, "CMakeCache.txt")
            dbg("found CMakeCache.txt:", cmakecache)
            ch = cmake.CMakeCache(pdir)
            self.build_dir = os.path.dirname(pdir)
            self.install_dir = os.path.dirname(ch['CMAKE_INSTALL_PREFIX'].val)
            self.root_dir = ch['CMAKE_HOME_DIRECTORY'].val
            self.cmakelists = os.path.join(self.root_dir, "CMakeLists.txt")
        else:
            self.build_dir = None
            self.install_dir = None
            self.root_dir = pdir
        #
        _saferealpath = lambda p: p if p is None else os.path.realpath(p)
        self.root_dir = _saferealpath(self.root_dir)
        self.build_dir = _saferealpath(self.build_dir)
        self.install_dir = _saferealpath(self.install_dir)
        self.cmakelists = _saferealpath(self.cmakelists)
        #
        dbg("root_dir:", self.root_dir)
        dbg("build_dir:", self.build_dir)
        dbg("install_dir:", self.install_dir)
        dbg("CMakeLists.txt:", self.cmakelists)
        #
        if not _pexists(self.cmakelists):
            raise err.CMakeListsNotFound(pdir)
        #
        if cmakecache is not None:
            self._init_with_build_dir(os.path.dirname(cmakecache), **kwargs)
        elif cmake.hascache(self.root_dir):
            self._init_with_build_dir(self.root_dir, **kwargs)
        elif kwargs.get('glob'):
            self._init_with_glob(**kwargs)
        else:
            self.load_configs()
            self._init_with_build_items(**kwargs)

    def _init_with_build_dir(self, pdir, **kwargs):
        build = Build.deserialize(pdir)
        self.builds = [build]

    def _init_with_glob(self, **kwargs):
        g = kwargs.get('glob')
        self.builds = []
        for pattern in g:
            bp = os.path.join(self.build_dir, pattern)
            li = glob.glob(bp)
            for b in li:
                build = Build.deserialize(b)
                self.builds.append(build)

    def _init_with_build_items(self, **kwargs):
        s, a, c, t, v = __class__.get_build_items(**kwargs)
        #
        cr = CombinationRules(kwargs.get('combination_rules', []))
        combs = cr.valid_combinations(s, a, c, t, v)
        dbg("combinations:", combs)
        self.combination_rules = cr
        #
        self.builds = []
        for comb in combs:
            dbg("adding build from combination:", comb)
            self.add_build(*comb) #s_, a_, c_, t_, v_)
        #
        self.systems = s
        self.architectures = a
        self.compilers = c
        self.build_types = t
        self.variants = v
        #
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
            _addnew(b, 'build_type')
            _addnew(b, 'compiler')
            _addnew(b, 'variant')

    @staticmethod
    def get_build_items(**kwargs):
        d = odict()
        for c, cls in (
                ('systems', System),
                ('architectures', Architecture),
                ('compilers', Compiler),
                ('build_types', BuildType),
                ('variants', Variant)):
            d[c] = (cls, kwargs.get(c))
        coll = BuildItem.create(d)
        s = coll['systems']
        a = coll['architectures']
        c = coll['compilers']
        t = coll['build_types']
        v = coll['variants']
        return s, a, c, t, v

    def load_configs(self):
        seq = [os.path.join(d, "cmany.yml") for d in (
            conf.CONF_DIR, conf.USER_DIR, self.root_dir)]
        if self.kwargs.get('no_default_config'):
            seq = []
        for f in self.kwargs.get('config_file', []):
            ff = f
            if not os.path.isabs(ff):
                ff = os.path.join(self.root_dir, ff)
            if not os.path.exists(ff):
                raise err.ConfigFileNotFound(ff)
            seq.append(f)
        self.configs = conf.Configs.load_seq(seq)

    def save_configs(self):
        # c = Configs()
        pass

    def create_proj(self):
        yml = CommentedMap()
        yml['project'] = CommentedMap()
        #
        def _add(name):
            items = getattr(self, name)
            #if BuildItem.trivial_item(items):
            #    yml['project'][name] = "_default_"
            #elif BuildItem.no_flags_in_collection(items):
            if BuildItem.no_flags_in_collection(items):
                out = []
                for s in items:
                    out.append(s.name)
                yml['project'][name] = out
            else:
                out = []
                for s in items:
                    cm = CommentedMap()
                    cm[s.name] = CommentedMap()
                    s.save_config(cm[s.name])
                    out.append(cm)
                yml['project'][name] = out
        #
        _add('systems')
        _add('architectures')
        _add('compilers')
        _add('build_types')
        _add('variants')
        txt = yaml.round_trip_dump(yml)
        fn = self.kwargs['output_file']
        if not os.path.isabs(fn):
            fn = os.path.join(self.root_dir, fn)
        with open(fn, "w") as f:
            f.write(txt)

    def add_build(self, system, arch, compiler, build_type, variant):
        # duplicate the build items, as they may be mutated due
        # to translation of their flags for the compiler
        def _dup_item(item):
            i = copy.deepcopy(item)
            i.flags.resolve_flag_aliases(compiler, aliases=self.configs.flag_aliases)
            return i
        s = _dup_item(system)
        a = _dup_item(arch)
        t = _dup_item(build_type)
        c = _dup_item(compiler)
        v = _dup_item(variant)
        #
        f = BuildFlags('all_builds', **self.kwargs)
        f.resolve_flag_aliases(compiler, aliases=self.configs.flag_aliases)
        #
        # create the build
        dbg("adding build:", s, a, t, c, v, f)
        b = Build(self.root_dir, self.build_dir, self.install_dir,
                  s, a, t, c, v, f,
                  self.num_jobs, dict(self.kwargs))
        #
        # When a build is created, its parameters may have been adjusted
        # because of an incompatible generator specification.
        # So drop this build if an equal one already exists
        if b.adjusted and self.exists(b):
            return False  # a similar build already exists
        #
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
        _h("build_type", "build_type")
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

    def reconfigure(self, **restrict_to):
        if not os.path.exists(self.build_dir):
            os.makedirs(self.build_dir)
        self._execute(Build.reconfigure, "Reconfigure", silent=False, **restrict_to)

    def export_compile_commands(self, **restrict_to):
        if not os.path.exists(self.build_dir):
            os.makedirs(self.build_dir)
        self._execute(Build.export_compile_commands, "Export compile commands", silent=False, **restrict_to)

    def build(self, **restrict_to):
        def do_build(build):
            build.build(self.targets)
        self._execute(do_build, "Build", silent=False, **restrict_to)

    def build_files(self, target, files):
        def do_build_files(build):
            build.build_files(target, files)
        self._execute(do_build_files, "BuildFiles", silent=False)

    def rebuild(self, **restrict_to):
        def do_rebuild(build):
            build.rebuild(self.targets)
        self._execute(do_rebuild, "Rebuild", silent=False, **restrict_to)

    def clean(self, **restrict_to):
        self._execute(Build.clean, "Clean", silent=False, **restrict_to)

    def install(self, **restrict_to):
        self._execute(Build.install, "Install", silent=False, **restrict_to)

    def reinstall(self, **restrict_to):
        self._execute(Build.reinstall, "Reinstall", silent=False, **restrict_to)

    def run_cmd(self, cmd, **subprocess_args):
        def run_it(build):
            build.run_custom_cmd(cmd, **subprocess_args)
        self._execute(run_it, "Run cmd", silent=False)

    def export_vs(self):
        confs = []
        for b in self.builds:
            confs.append(b.json_data())
        jd = odict([('configurations', confs)])
        with open(self.configfile, 'w') as f:
            json.dump(jd, f, indent=2)

    def show_vars(self, varlist):
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

    def show_build_names(self):
        for b in self.builds:
            print(b)

    def show_build_dirs(self):
        for b in self.builds:
            print(b.builddir)

    def show_builds(self):
        for b in self.builds:
            b.show_properties()

    def show_targets(self):
        for t in self.builds[0].get_targets():
            print(t)

    def _execute(self, fn, msg, silent, **restrict_to):
        builds = self.select(**restrict_to)
        failed = odict()
        durations = odict()
        num = len(builds)
        if not silent:
            if num == 0:
                print("no builds selected")
        if num == 0:
            return
        def nt(*args, **kwargs):  # notice
            if silent: return
            util.lognotice(*args, **kwargs)
        def dn(*args, **kwargs):  # done
            if silent: return
            util.logdone(*args, **kwargs)
        def er(*args, **kwargs):  # error
            if silent: return
            util.logerr(*args, **kwargs)
        #
        if num > 1:
            nt("")
            nt("===============================================")
            nt(msg + ": start", num, "builds:")
            for b in builds:
                nt(b)
            nt("===============================================")
        #
        for i, b in enumerate(builds):
            if i > 0:
                nt("\n")
            nt("-----------------------------------------------")
            if num > 1:
                nt(msg + ": build #{} of {}:".format(i + 1, num), b)
            else:
                nt(msg, b)
            nt("-----------------------------------------------")
            #
            t = timeit.default_timer()
            try:
                # this is where it happens
                fn(b)  # <-- here
                word, logger = "finished", dn
            # exceptions thrown from builds inherit this type
            except err.BuildError as e:
                word, logger = "failed", er
                util.logerr(f"{b} failed! {e}")
                failed[b] = e
                if not self.continue_on_fail:
                    raise
            t = timeit.default_timer() - t
            hrt = util.human_readable_time(t)
            durations[b] = (t, hrt)
            if num > 1:
                ip1 = i + 1
                info = f"{word} build #{ip1} of {num} ({hrt})"
            else:
                info = f"{word} building ({hrt})"
            logger(msg + ": " + info + ":",  b)
        #
        nt("-----------------------------------------------")
        if num > 1:
            if failed:
                dn(msg + ": processed", num, "builds: (with failures)")
            else:
                dn(msg + ": finished", num, "builds:")
            tot = 0.
            for _, (d, _) in durations.items():
                tot += d
            for b in builds:
                dur, hrt = durations[b]
                times = "({}, {:.3f}%, {:.3f}x avg)".format(
                    hrt, dur / tot * 100., dur / (tot / float(num))
                )
                fail = failed.get(b)
                if fail:
                    er(b, times, "[FAIL]!!!", fail)
                else:
                    dn(b, times)
            if failed:
                msg = "{}/{} builds failed ({:.1f}%)!"
                er(msg.format(len(failed), num, float(len(failed)) / num * 100.0))
            else:
                dn(f"all {num} builds succeeded!")
            dn("total time:", util.human_readable_time(tot))
            nt("===============================================")
        if failed:
            raise Exception(failed)
