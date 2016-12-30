#!/usr/bin/env python3

import os
import sys
import re
import glob
import json
import argparse
from datetime import datetime as datetime
from collections import OrderedDict as odict
from multiprocessing import cpu_count as cpu_count

from .conf import *
from .util import *
from .cmake_sysinfo import *
from .vsinfo import *


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
        # if not hasattr(System, "_current"):
        #     if sys.platform == "linux" or sys.platform == "linux2":
        #         System._current = System("linux")
        #     elif sys.platform == "darwin":
        #         System._current = System("mac")
        #     elif sys.platform == "win32":
        #         System._current = System("windows")
        #     else:
        #         raise Exception("unknown system")
        # return System._current


# -----------------------------------------------------------------------------
class Architecture(BuildItem):
    """Specifies a processor architecture"""

    @staticmethod
    def default():
        """return the architecture of the current machine"""
        return Architecture(__class__.default_str())

    @staticmethod
    def default_str():
        s = CMakeSysInfo.architecture()
        if s == "amd64":
            s = "x86_64"
        return s
        # # http://stackoverflow.com/a/12578715/5875572
        # import platform
        # machine = platform.machine()
        # if machine.endswith('64'):
        #     return Architecture('x86_64')
        # elif machine.endswith('86'):
        #     return Architecture('x32')
        # raise Exception("unknown architecture")

    @property
    def is64(self):
        def fn():
            s = re.search('64', self.name)
            return s is not None
        return cacheattr(self, "_is64", fn)

    @property
    def is32(self):
        return not self.is64

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
        self.macros = []

    def merge(self, other):
        """other will take precedence, ie, their options will come last"""
        c = CompileOptions()
        c.name = self.name+"+"+other.name
        c.cmake_flags = self.cmake_flags + other.cmake_flags
        c.cflags = self.cflags + other.cflags
        c.lflags = self.lflags + other.lflags
        c.macros = self.macros + other.macros
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
            vs = VisualStudioInfo.find_any()
            cpp = vs.name if vs is not None else CMakeSysInfo.cxx_compiler()
        return cpp

    def __init__(self, path):
        if path.startswith("vs") or path.startswith("Visual Studio"):
            vs = VisualStudioInfo(path)
            self.vs = vs
            path = vs.cxx_compiler
        else:
            p = which(path)
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
        if shortname == "icc":
            cc = re.sub(r'icpc', r'icc', cxx_compiler)
        elif shortname == "gcc":
            cc = re.sub(r'g\+\+', r'gcc', cxx_compiler)
        elif shortname == "clang":
            cc = re.sub(r'clang\+\+', r'clang', cxx_compiler)
        else:
            cc = cxx_compiler
        return cc

    def get_version(self, path):
        # is this visual studio?
        if hasattr(self, "vs"):
            return self.vs.name, str(self.vs.year), self.vs.name
        # # other compilers
        # print("cmp: found compiler:", name, path)
        out = runsyscmd([path, '--version'], echo_cmd=False, echo_output=False, capture_output=True).strip("\n")
        version_full = out.split("\n")[0]
        splits = version_full.split(" ")
        name = splits[0].lower()
        # print("cmp: version:", name, "---", firstline, "---")
        vregex = r'(\d+\.\d+)\.\d+'
        if name.startswith("g++") or name.startswith("gcc"):
            name = "gcc"
            version = runsyscmd([path, '-dumpversion'], echo_cmd=False, echo_output=False, capture_output=True).strip("\n")
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
            version = runsyscmd([path, '--dumpversion'], echo_cmd=False, echo_output=False, capture_output=True).strip("\n")
            version = re.sub(vregex, r'\1', version)
        #
        return name, version, version_full


# -----------------------------------------------------------------------------
class Variant(BuildItem):
    """for variations in compile options"""

    def __init__(self, name):
        super().__init__(name)
        self.options = CompileOptions()


# -----------------------------------------------------------------------------
class Generator(BuildItem):

    """Visual Studio aliases example:
    vs2013: use the bitness of the default OS
    vs2013_32: use 32bit version
    vs2013_64: use 64bit version
    """

    @staticmethod
    def default():
        return Generator(__class__.default_str(), cpu_count())

    @staticmethod
    def default_str():
        s = CMakeSysInfo.generator()
        return s

    @staticmethod
    def create_default(system, arch, compiler, num_jobs):
        if not compiler.is_msvc:
            if System.default_str() == "windows":
                return Generator("Unix Makefiles", num_jobs)
            else:
                return Generator(__class__.default_str(), num_jobs)
        else:
            return Generator(compiler.name, num_jobs)

    @staticmethod
    def resolve_alias(gen):
        if gen.startswith('vs') or gen.startswith('Visual Studio'):
            return VisualStudioInfo.to_gen(gen)
        return gen

    def __init__(self, name, num_jobs):
        if name.startswith('vs'):
            n = name
            name = VisualStudioInfo.to_gen(name)
        self.alias = name
        super().__init__(name)
        self.num_jobs = num_jobs
        self.is_makefile = name.endswith("Makefiles")
        self.is_ninja = name.endswith("Ninja")
        self.is_msvc = name.startswith("Visual Studio")

    def configure_args(self, build):
        if self.name != "":
            if self.is_msvc and build.compiler.vs.toolset is not None:
                return ['-G', '"{}"'.format(self.name), '-T', build.compiler.vs.toolset]
            else:
                return ['-G', '"{}"'.format(self.name)]
        else:
            return []

    def cmd(self, targets, build):
        if self.is_makefile:
            return ['make', '-j', str(self.num_jobs)] + targets
        elif self.is_msvc:
            if not hasattr(self, "sln"):
                sln_files = glob.glob("*.sln")
                if len(sln_files) != 1:
                    raise Exception("there's more than one solution file in the project folder")
                self.sln = sln_files[0]
            return [build.compiler.vs.msbuild, self.sln,
                    '/maxcpucount:'+str(self.num_jobs),
                    '/property:Configuration='+str(build.buildtype),
                    '/target:'+';'.join(targets)]
        else:
            return ['cmake', '--build', '.', '--config', str(build.buildtype) ] + ['--target '+ t for t in targets ]

    def install(self, build):
        return ['cmake', '--build', '.', '--config', str(build.buildtype), '--target', 'install']

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
                 system, arch, buildtype, compiler, variant,
                 num_jobs):
        self.generator = Generator.create_default(sys, arch, compiler, num_jobs)
        self.system = system
        self.architecture = arch
        self.buildtype = buildtype
        self.compiler = compiler
        self.variant = variant
        # self.crosscompile = (system != System.default())
        # self.toolchain = None
        self.projdir = chkf(proj_root)
        self.buildroot = os.path.abspath(build_root)
        self.builddir = os.path.abspath(os.path.join(build_root, self._cat("-", for_build_dir=True)))
        self.preload_file = os.path.join(self.builddir, Build.pfile)
        self.installroot = os.path.abspath(install_root)
        self.installdir = os.path.join(self.installroot, self._cat("-", for_build_dir=False))

    def __repr__(self):
        return self._cat("-", for_build_dir=False)

    def _cat(self, sep, for_build_dir):
        if self.compiler.is_msvc and for_build_dir:
            s = "{1}{0}{2}{0}{3}"
            s = s.format(sep, self.system, self.architecture, self.compiler)
        else:
            s = "{1}{0}{2}{0}{3}{0}{4}"
            s = s.format(sep, self.system, self.architecture, self.compiler, self.buildtype)
        if self.variant:
            s += "{0}{1}".format(sep, self.variant)
        return s

    def create_dir(self):
        if not os.path.exists(self.builddir):
            os.makedirs(self.builddir)

    def _gather_flags(self):
        # flags = self.generator.compile_flags()
        # flags += self.compiler.
        # return flags
        return []

    def create_preload_file(self):
        # http://stackoverflow.com/questions/17597673/cmake-preload-script-for-cache
        self.create_dir()
        lines = []
        def _s(var, value, type): lines.append('_cmany_set({} "{}" {})'.format(var, value, type))
        def s(var, value): _s(var, value, "STRING")
        def p(var, value): _s(var, re.sub(r'\\', '/', value), "PATH")
        def f(var, value): _s(var, re.sub(r'\\', '/', value), "FILEPATH")

        p("CMAKE_INSTALL_PREFIX", self.installdir)
        f("CMAKE_CXX_COMPILER", self.compiler.path)
        f("CMAKE_C_COMPILER", self.compiler.c_compiler)
        s("CMAKE_BUILD_TYPE", self.buildtype)
        flags = self._gather_flags()
        if flags:
            s('CMAKE_CXX_FLAGS', " ".join(flags))

        now = datetime.now().strftime("%Y/%m/%d %H:%m")
        txt = __class__.preload_file_tpl.format(date=now, vars="\n".join(lines))
        with open(self.preload_file, "w") as f:
            f.write(txt)
        return self.preload_file

    def configure(self):
        self.create_dir()
        if not os.path.exists(self.preload_file):
            self.create_preload_file()
        with setcwd(self.builddir):
            cmd = (['cmake', '-C', os.path.basename(self.preload_file),]
                   + self.generator.configure_args(self) +
                   [# '-DCMAKE_TOOLCHAIN_FILE='+toolchain_file,
                   self.projdir])
            runsyscmd(cmd, echo_output=True)
            with open("cmany_configure.done", "w") as f:
                f.write(" ".join(cmd) + "\n")

    def build(self, targets = []):
        self.create_dir()
        with setcwd(self.builddir):
            if not os.path.exists("cmany_configure.done"):
                self.configure()
            if self.compiler.is_msvc and len(targets) == 0:
                targets = ["ALL_BUILD"]
            cmd = self.generator.cmd(targets, self)
            runsyscmd(cmd, echo_output=True)
            with open("cmany_build.done", "w") as f:
                f.write(" ".join(cmd) + "\n")

    def install(self):
        self.create_dir()
        with setcwd(self.builddir):
            if not os.path.exists("cmany_build.done"):
                self.build()
            cmd = self.generator.install(self)
            print(cmd)
            runsyscmd(cmd, echo_output=True)

    def clean(self):
        self.create_dir()
        with setcwd(self.builddir):
            cmd = self.generator.cmd(['clean'], self)
            runsyscmd(cmd, echo_output=True)
            os.remove("cmany_build.done")

    def getvars(self, varlist):
        vlist = [v + ':' for v in varlist]
        values = odict()
        rx = r'(^.*?)=(.*)$'
        with setcwd(self.builddir, silent=True):
            with open('CMakeCache.txt') as f:
                for line in f:
                    for v in vlist:
                        if line.startswith(v):
                            ls = line.strip()
                            vt = re.sub(rx, r'\1', ls)
                            values[vt] = re.sub(rx, r'\2', ls)
        return values

    preload_file_tpl = """
# Do not edit. Will be overwritten.
# Generated by cmany on {date}

if(NOT _cmany_def)
    set(_cmany_def ON)
    function(_cmany_set var value type)
        set(${{var}} "${{value}}" CACHE ${{type}} "")
        message(STATUS "cmany: ${{var}}=${{value}}")
    endfunction(_cmany_set)
endif(NOT _cmany_def)

message(STATUS "cmany:preload----------------------")
{vars}
message(STATUS "cmany:preload----------------------")

# Do not edit. Will be overwritten.
# Generated by cmany on {date}
"""

# -----------------------------------------------------------------------------
class ProjectConfig:

    # @staticmethod
    # def default_systems():
    #     return ctor(System, ["linux", "windows", "android", "ios", "ps4", "xboxone"])
    # @staticmethod
    # def default_architectures():
    #     return ctor(Architecture, ["x86", "x86_64", "arm"])
    # @staticmethod
    # def default_buildtypes():
    #     return ctor(BuildType, ["Debug", "Release"])
    # @staticmethod
    # def default_compilers():
    #     return ctor(Compiler, ["clang++", "g++", "icpc"])
    # # no default variants

    def __init__(self, **kwargs):
        projdir = kwargs.get('proj_dir', os.getcwd())
        self.rootdir = os.getcwd() if projdir == "." else projdir
        self.cmakelists = chkf(self.rootdir, "CMakeLists.txt")
        self.builddir = kwargs.get('build_dir', os.path.join(os.getcwd(), "build"))
        self.installdir = kwargs.get('install_dir', os.path.join(os.getcwd(), "install"))

        def _get(name, class_):
            g = kwargs.get(name)
            if g is None or not g:
                g = [class_.default()] if class_ is not None else [None]
                return g
            l = []
            for i in g:
                l.append(class_(i))
            return l
        self.systems = _get('systems', System)
        self.architectures = _get('architectures', Architecture)
        self.buildtypes = _get('build_types', BuildType)
        self.compilers = _get('compilers', Compiler)
        self.variants = _get('variants', None)

        #self.generator = Generator(kwargs.get('generator'))
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
                  system, arch, buildtype, compiler, variant,
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
        builds = self.select_and_show(**restrict_to)
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

    def showvars(self, varlist, **restrict_to):
        varv = odict()
        def getv(build):
            for k,v in Build.getvars(build, varlist).items():
                sk = str(k)
                if not varv.get(sk): varv[sk] = odict()
                varv[sk][str(build)] = v
        self._execute(getv, "", silent=True, **restrict_to)
        for var,sysvalues in varv.items():
            for s,v in sysvalues.items():
                print("{}='{}' ({})".format(var, v, s))

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
