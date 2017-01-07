#!/usr/bin/env python3

import os
import sys
import re
import glob
from datetime import datetime
from collections import OrderedDict as odict
from multiprocessing import cpu_count as cpu_count

from . import util
from .cmake_sysinfo import CMakeSysInfo, CMakeCache, getcachevars
from . import vsinfo
from . import cflags


# -----------------------------------------------------------------------------
class BuildItem:
    """A base class for build items."""

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


# -----------------------------------------------------------------------------
class BuildType(BuildItem):
    """Specifies a build type, ie, one of Release, Debug, etc"""

    @staticmethod
    def default():
        return BuildType("Release")


# -----------------------------------------------------------------------------
class System(BuildItem):
    """Specifies an operating system"""

    @staticmethod
    def default():
        """return the current operating system"""
        return System(__class__.default_str())

    @staticmethod
    def default_str():
        s = CMakeSysInfo.system_name()
        if s == "mac os x" or s == "Darwin":
            s = "mac"
        return s


# -----------------------------------------------------------------------------
class Architecture(BuildItem):
    """Specifies a processor architecture"""

    @staticmethod
    def default():
        """return the architecture of the current machine"""
        return Architecture(__class__.default_str())

    @staticmethod
    def default_str():
        # s = CMakeSysInfo.architecture()
        # if s == "amd64":
        #     s = "x86_64"
        # return s
        if util.in_64bit():
            return "x86_64"
        elif util.in_32bit():
            return "x86"

    @property
    def is64(self):
        def fn():
            s = re.search('64', self.name)
            return s is not None
        return util.cacheattr(self, "_is64", fn)

    @property
    def is32(self):
        return not self.is64 and not self.is_arm

    @property
    def is_arm(self):
        return "arm" in self.name.lower()


# -----------------------------------------------------------------------------
class CompileOptions:

    def __init__(self, name=""):
        self.name = name
        self.cmake_flags = []
        self.cflags = []
        self.lflags = []

    def merge(self, other):
        """other will take precedence, ie, their options will come last"""
        c = CompileOptions()
        c.name = self.name+"+"+other.name
        c.cmake_flags = self.cmake_flags + other.cmake_flags
        c.cflags = self.cflags + other.cflags
        c.lflags = self.lflags + other.lflags
        return c

# -----------------------------------------------------------------------------
class Compiler(BuildItem):
    """Specifies a compiler"""

    @staticmethod
    def default():
        return Compiler(__class__.default_str())

    @staticmethod
    def default_str():
        if str(System.default()) != "windows":
            cpp = CMakeSysInfo.cxx_compiler()
        else:
            vs = vsinfo.find_any()
            cpp = vs.name if vs is not None else CMakeSysInfo.cxx_compiler()
        return cpp

    def __init__(self, path):
        if path.startswith("vs") or path.startswith("Visual Studio"):
            vs = vsinfo.VisualStudioInfo(path)
            self.vs = vs
            path = vs.cxx_compiler
        else:
            p = util.which(path)
            if p is None:
                raise Exception("compiler not found: " + path)
            if p != path:
                print("compiler: selected {} for {}".format(p, path))
            path = os.path.abspath(p)
        name, version, version_full = self.get_version(path)
        self.shortname = name
        self.gcclike = self.shortname in ('gcc', 'clang', 'icc')
        self.is_msvc = self.shortname.startswith('vs')
        if not self.is_msvc:
            name += version
        self.path = path
        self.version = version
        self.version_full = version_full
        super().__init__(name)
        self.c_compiler = __class__.get_c_compiler(self.shortname, self.path)

    @staticmethod
    def get_c_compiler(shortname, cxx_compiler):
        # if cxx_compiler.endswith("c++") or cxx_compiler.endswith('c++.exe'):
        #     cc = re.sub(r'c\+\+', r'cc', cxx_compiler)
        if shortname.startswith('vs') or re.search(r'sual Studio', cxx_compiler):
            cc = cxx_compiler
        elif shortname == "icc":
            cc = re.sub(r'icpc', r'icc', cxx_compiler)
        elif shortname == "gcc":
            cc = re.sub(r'g\+\+', r'gcc', cxx_compiler)
        elif shortname == "clang":
            cc = re.sub(r'clang\+\+', r'clang', cxx_compiler)
        elif shortname == "c++":
            cc = "cc"
        else:
            cc = "cc"
        return cc

    def get_version(self, path):

        def slntout(cmd):
            out = util.runsyscmd(cmd, echo_cmd=False,
                                 echo_output=False, capture_output=True)
            out = out.strip("\n")
            return out

        # is this visual studio?
        if hasattr(self, "vs"):
            return self.vs.name, str(self.vs.year), self.vs.name
        # # other compilers
        # print("cmp: found compiler:", name, path)
        out = slntout([path, '--version'])
        version_full = out.split("\n")[0]
        splits = version_full.split(" ")
        name = splits[0].lower()
        # print("cmp: version:", name, "---", firstline, "---")
        vregex = r'(\d+\.\d+)\.\d+'
        if name.startswith("g++") or name.startswith("gcc"):
            name = "gcc"
            version = slntout([path, '-dumpversion'])
            version = re.sub(vregex, r'\1', version)
            # print("gcc version:", version, "---")
        elif name.startswith("clang"):
            name = "clang"
            version = re.sub(r'clang version ' + vregex + '.*', r'\1', version_full)
            # print("clang version:", version, "---")
        elif name.startswith("icpc"):
            name = "icc"
            version = re.sub(r'icpc \(ICC\) ' + vregex + '.*', r'\1', version_full)
            # print("icc version:", version, "---")
        else:
            version = slntout([path, '-dumpversion'])
            version = re.sub(vregex, r'\1', version)
        #
        return name, version, version_full


# -----------------------------------------------------------------------------
class Variant(BuildItem):
    """for variations in compile options"""

    def __init__(self, name):
        super().__init__(name)
        self.options = CompileOptions(name)


# -----------------------------------------------------------------------------
class Generator(BuildItem):

    """Visual Studio aliases example:
    vs2013: use the bitness of the current system
    vs2013_32: use 32bit version
    vs2013_64: use 64bit version
    """

    @staticmethod
    def default():
        return Generator(__class__.default_str(), cpu_count())

    @staticmethod
    def default_str():
        """get the default generator from cmake"""
        s = CMakeSysInfo.generator()
        return s

    @staticmethod
    def create(build, num_jobs, fallback_generator="Unix Makefiles"):
        """create a compiler """
        if build.compiler.is_msvc:
            return Generator(build.compiler.name, build, num_jobs)
        else:
            if str(build.system) == "windows":
                return Generator(fallback_generator, build, num_jobs)
            else:
                return Generator(__class__.default_str(), build, num_jobs)

    def __init__(self, name, build, num_jobs):
        if name.startswith('vs'):
            name = vsinfo.to_gen(name)
        self.alias = name
        super().__init__(name)
        self.num_jobs = num_jobs
        self.is_makefile = name.endswith("Makefiles")
        self.is_ninja = name.endswith("Ninja")
        self.is_msvc = name.startswith("Visual Studio")
        self.build = build
        #
        self.full_name = self.name
        if self.is_msvc:
            ts = build.compiler.vs.toolset
            self.full_name += ts if ts is not None else ""
        self.full_name += " ".join(self.build.flags.cmake_flags)

    def configure_args(self):
        if self.name != "":
            if self.is_msvc and self.build.compiler.vs.toolset is not None:
                args = ['-G', self.name, '-T', self.build.compiler.vs.toolset]
            else:
                args = ['-G', self.name]
        else:
            args = []
        args += self.build.flags.cmake_flags
        return args

    def cmd(self, targets):
        if self.is_makefile:
            return ['make', '-j', str(self.num_jobs)] + targets
        elif self.is_msvc:
            if not hasattr(self, "sln"):
                sln_files = glob.glob("*.sln")
                if len(sln_files) != 1:
                    raise Exception("there's more than one solution file in the project folder")
                self.sln = sln_files[0]
            return [self.build.compiler.vs.msbuild, self.sln,
                    '/maxcpucount:' + str(self.num_jobs),
                    '/property:Configuration=' + str(self.build.buildtype),
                    '/target:' + ';'.join(targets)]
        else:
            bt = str(self.build.buildtype)
            return (['cmake', '--build', '.', '--config', bt] +
                    ['--target ' + t for t in targets])

    def install(self):
        bt = str(self.build.buildtype)
        return ['cmake', '--build', '.', '--config', bt, '--target', 'install']

    """
    generators: https://cmake.org/cmake/help/v3.7/manual/cmake-generators.7.html

    Unix Makefiles
    MSYS Makefiles
    MinGW Makefiles
    NMake Makefiles
    Ninja
    Watcom WMake
    CodeBlocks - Ninja
    CodeBlocks - Unix Makefiles
    CodeBlocks - MinGW Makefiles
    CodeBlocks - NMake Makefiles
    CodeLite - Ninja
    CodeLite - Unix Makefiles
    CodeLite - MinGW Makefiles
    CodeLite - NMake Makefiles
    Eclipse CDT4 - Ninja
    Eclipse CDT4 - Unix Makefiles
    Eclipse CDT4 - MinGW Makefiles
    Eclipse CDT4 - NMake Makefiles
    KDevelop3
    KDevelop3 - Unix Makefiles
    Kate - Ninja
    Kate - Unix Makefiles
    Kate - MinGW Makefiles
    Kate - NMake Makefiles
    Sublime Text 2 - Ninja
    Sublime Text 2 - Unix Makefiles
    Sublime Text 2 - MinGW Makefiles
    Sublime Text 2 - NMake Makefiles

    Visual Studio 6
    Visual Studio 7
    Visual Studio 7 .NET 2003
    Visual Studio 8 2005 [Win64|IA64]
    Visual Studio 9 2008 [Win64|IA64]
    Visual Studio 10 2010 [Win64|IA64]
    Visual Studio 11 2012 [Win64|ARM]
    Visual Studio 12 2013 [Win64|ARM]
    Visual Studio 14 2015 [Win64|ARM]
    Visual Studio 15 2017 [Win64|ARM]

    Green Hills MULTI
    Xcode
    """


# -----------------------------------------------------------------------------
class Build:
    """Holds a build's settings"""

    pfile = "cmany_preload.cmake"

    def __init__(self, proj_root, build_root, install_root,
                 system, arch, buildtype, compiler, variant, flags,
                 num_jobs):
        self.system = system
        self.architecture = arch
        self.buildtype = buildtype
        self.compiler = compiler
        self.variant = variant
        self.flags = flags
        # self.crosscompile = (system != System.default())
        # self.toolchain = None
        self.tag = self._cat('-')
        self.projdir = util.chkf(proj_root)
        self.buildroot = os.path.abspath(build_root)
        self.buildtag = self.tag
        self.builddir = os.path.abspath(os.path.join(build_root, self.buildtag))
        self.installroot = os.path.abspath(install_root)
        self.installtag = self.tag
        self.installdir = os.path.join(self.installroot, self.installtag)
        self.preload_file = os.path.join(self.builddir, Build.pfile)
        self.generator = Generator.create(self, num_jobs)
        # this will load the vars from the builddir cache, if it exists
        self.cachefile = os.path.join(self.builddir, 'CMakeCache.txt')
        self.varcache = CMakeCache(self.builddir)
        # ... and this will overwrite (in memory) the vars with the input
        # arguments. This will make the cache dirty and so we know when it
        # needs to be committed back to CMakeCache.txt
        self.gather_cache_vars()

    def __repr__(self):
        return self.tag

    def _cat(self, sep):
        s = "{1}{0}{2}{0}{3}{0}{4}"
        s = s.format(sep, self.system, self.architecture, self.compiler, self.buildtype)
        if self.variant:
            s += "{0}{1}".format(sep, self.variant)
        return s

    def gather_cache_vars(self):
        vc = self.varcache
        vc.p('CMAKE_INSTALL_PREFIX', self.installdir, from_input=True)
        if not self.generator.is_msvc:
            vc.f('CMAKE_CXX_COMPILER', self.compiler.path, from_input=True)
            vc.f('CMAKE_C_COMPILER', self.compiler.c_compiler, from_input=True)
        vc.s('CMAKE_BUILD_TYPE', str(self.buildtype), from_input=True)
        flags = self._gather_flags('cflags')
        if flags:
            vc.s('CMAKE_CXX_FLAGS', ' '.join(flags), from_input=True)

    def create_dir(self):
        if not os.path.exists(self.builddir):
            os.makedirs(self.builddir)

    def configure(self):
        self.create_dir()
        self.create_preload_file()
        if self.needs_cache_regeneration():
            self.varcache.commit(self.builddir)
        with util.setcwd(self.builddir):
            cmd = (['cmake', '-C', os.path.basename(self.preload_file)]
                   + self.generator.configure_args() +
                   [  # '-DCMAKE_TOOLCHAIN_FILE='+toolchain_file,
                   self.projdir])
            util.runsyscmd(cmd)
            self.mark_configure_done(cmd)

    def mark_configure_done(self, cmd):
        with util.setcwd(self.builddir):
            with open("cmany_configure.done", "w") as f:
                f.write(" ".join(cmd) + "\n")

    def needs_configure(self):
        if not os.path.exists(self.builddir):
            return True
        with util.setcwd(self.builddir):
            if not os.path.exists("cmany_configure.done"):
                return True
            if self.needs_cache_regeneration():
                return True
        return False

    def needs_cache_regeneration(self):
        if os.path.exists(self.cachefile) and self.varcache.dirty:
            return True
        return False

    def build(self, targets=[]):
        self.create_dir()
        with util.setcwd(self.builddir):
            if self.needs_configure():
                self.configure()
            if self.compiler.is_msvc and len(targets) == 0:
                targets = ["ALL_BUILD"]
            cmd = self.generator.cmd(targets)
            util.runsyscmd(cmd)
            self.mark_build_done(cmd)

    def mark_build_done(self, cmd):
        with util.setcwd(self.builddir):
            with open("cmany_build.done", "w") as f:
                f.write(" ".join(cmd) + "\n")

    def needs_build(self):
        if not os.path.exists(self.builddir):
            return True
        with util.setcwd(self.builddir):
            if not os.path.exists("cmany_build.done"):
                return True
        return False

    def install(self):
        self.create_dir()
        with util.setcwd(self.builddir):
            if self.needs_build():
                self.build()
            cmd = self.generator.install()
            print(cmd)
            util.runsyscmd(cmd)

    def clean(self):
        self.create_dir()
        with util.setcwd(self.builddir):
            cmd = self.generator.cmd(['clean'])
            util.runsyscmd(cmd)
            os.remove("cmany_build.done")

    def _gather_flags(self, which):
        flags = [CMakeSysInfo.var('CMAKE_CXX_FLAGS_INIT', self.generator)]
        for wf in getattr(self.flags, which):
            f = wf.get(self.compiler.shortname)
            if f:
                flags.append(f)
        return flags

    def create_preload_file(self):
        # http://stackoverflow.com/questions/17597673/cmake-preload-script-for-cache
        self.create_dir()
        lines = []
        s = '_cmany_set({} "{}" {})'
        for _, v in self.varcache.items():
            if v.from_input:
                lines.append(s.format(v.name, v.val, v.vartype))
        if lines:
            tpl = __class__.preload_file_tpl
        else:
            tpl = __class__.preload_file_tpl_empty
        now = datetime.now().strftime("%Y/%m/%d %H:%m")
        txt = tpl.format(date=now, vars="\n".join(lines))
        with open(self.preload_file, "w") as f:
            f.write(txt)
        return self.preload_file

    preload_file_tpl = """# Do not edit. Will be overwritten.
# Generated by cmany on {date}

if(NOT _cmany_set_def)
    set(_cmany_set_def ON)
    function(_cmany_set var value type)
        set(${{var}} "${{value}}" CACHE ${{type}} "")
        message(STATUS "cmany: ${{var}}=${{value}}")
    endfunction(_cmany_set)
endif(NOT _cmany_set_def)

message(STATUS "cmany:preload----------------------")
{vars}
message(STATUS "cmany:preload----------------------")

# Do not edit. Will be overwritten.
# Generated by cmany on {date}
"""
    preload_file_tpl_empty = """# Do not edit. Will be overwritten.
# Generated by cmany on {date}

message(STATUS "cmany: nothing to preload...")
"""

# -----------------------------------------------------------------------------
class ProjectConfig:

    def __init__(self, **kwargs):
        _get = lambda n,c: __class__._getarglist(n, c, **kwargs)
        projdir = kwargs.get('proj_dir', os.getcwd())
        self.rootdir = os.getcwd() if projdir == "." else projdir
        self.cmakelists = util.chkf(self.rootdir, "CMakeLists.txt")
        self.builddir = kwargs.get('build_dir', os.path.join(os.getcwd(), "build"))
        self.installdir = kwargs.get('install_dir', os.path.join(os.getcwd(), "install"))
        self.systems = _get('systems', System)
        self.architectures = _get('architectures', Architecture)
        self.buildtypes = _get('build_types', BuildType)
        self.compilers = _get('compilers', Compiler)
        self.variants = _get('variants', None)
        self.flags = CompileOptions('all_builds')
        self.flags.cmake_flags = kwargs['kflags']
        self.flags.cflags = cflags.asflags(kwargs['cflags'])
        self.flags.lflags = cflags.asflags(kwargs['lflags'])

        # self.generator = Generator(kwargs.get('generator'))
        self.num_jobs = kwargs.get('jobs')

        configfile = os.path.join(projdir, "cmany.json")
        self.configfile = None
        if os.path.exists(configfile):
            self.parse_file(configfile)
            self.configfile = configfile

        self.builds = []
        for s in self.systems:
            for a in self.architectures:
                for c in self.compilers:
                    for m in self.buildtypes:
                        for v in self.variants:
                            self.add_build_if_valid(s, a, m, c, v)

    def parse_file(self, configfile):
        raise Exception("not implemented")

    def add_build_if_valid(self, system, arch, buildtype, compiler, variant):
        if not self.is_valid(system, arch, buildtype, compiler, variant):
            return False
        b = Build(self.rootdir, self.builddir, self.installdir,
                  system, arch, buildtype, compiler, variant, self.flags,
                  self.num_jobs)
        self.builds.append(b)
        return True

    def is_valid(self, sys, arch, mode, compiler, variant):
        # TODO
        return True

    def select(self, **kwargs):
        out = [b for b in self.builds]

        def _h(li, kw, attr):
            g = kwargs.get(kw)
            if g is None:
                return li
            else:
                lo = []
                for b in li:
                    if str(getattr(b, attr)) == g:
                        lo.append(b)
            return lo
        out = _h(out, "sys", "system")
        out = _h(out, "arch", "architecture")
        out = _h(out, "buildtype", "buildtype")
        out = _h(out, "compiler", "compiler")
        out = _h(out, "variant", "variant")
        return out

    def create_tree(self, **restrict_to):
        builds = self.select(**restrict_to)
        for b in builds:
            b.create_dir()
            b.create_preload_file()
            # print(b, ":", d)

    def configure(self, **restrict_to):
        if not os.path.exists(self.builddir):
            os.makedirs(self.builddir)
        self._execute(Build.configure, "Configuring", silent=False, **restrict_to)

    def build(self, **restrict_to):
        self._execute(Build.build, "Building", silent=False, **restrict_to)

    def clean(self, **restrict_to):
        self._execute(Build.clean, "Cleaning", silent=False, **restrict_to)

    def install(self, **restrict_to):
        self._execute(Build.install, "Installing", silent=False, **restrict_to)

    def _execute(self, fn, msg, silent, **restrict_to):
        builds = self.select(**restrict_to)
        num = len(builds)
        if not silent:
            if num > 0:
                print("selected builds:")
                for b in builds:
                    print(b)
            else:
                print("no builds selected")
        if num == 0:
            return
        if not silent:
            print("")
            print("===============================================")
            if num > 1:
                print(msg + ": start", num, "builds")
                print("===============================================")
        for i, b in enumerate(builds):
            if not silent:
                if i > 0:
                    print("\n")
                print("-----------------------------------------------")
                if num > 1:
                    print(msg + ": build #{} of {}:".format(i+1, num), b)
                else:
                    print(msg, b)
                print("-----------------------------------------------")
            fn(b)
        if not silent:
            if num > 1:
                print("-----------------------------------------------")
                print(msg + ": finished", num, "builds")
            print("===============================================")

    @staticmethod
    def _getarglist(name, class_, **kwargs):
        g = kwargs.get(name)
        if g is None or not g:
            g = [class_.default()] if class_ is not None else [None]
            return g
        l = []
        for i in g:
            l.append(class_(i))
        return l

    def showvars(self, varlist):
        varv = odict()
        pat = os.path.join(self.builddir, '*', 'CMakeCache.txt')
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
