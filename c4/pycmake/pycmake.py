#!/usr/bin/env python3

import os
import subprocess
import sys
import re
from datetime import datetime as datetime
from collections import OrderedDict as odict
from multiprocessing import cpu_count as cpu_count

def which(cmd):
    if os.path.exists(cmd):
        return cmd
    for path in os.environ["PATH"].split(os.pathsep):
        j = os.path.join(path, cmd)
        if os.path.exists(j):
                return j
    return None      

def find_executable(name):
    for suf in ["",".exe"]:
        n = name + suf
        w = which(n)
        if w is not None:
            return w
    return None

def get_executable(name):
    w = find_executable(name)
    if w is None:
        raise Exception("could not find executable named " + name)
    return w

def choose_executable(purpose, *candidates):
    for c in candidates:
        if c is None:
            continue
        f = which(c)
        print("chooexe: ", c, f)
        if f is not None:
            return f
    err = "could not find executable for {}. Tried the following: {}"
    raise Exception(err.format(purpose, *var(candidates)))

def chkf(*args):
    "join the args as a path and check whether that path exists"
    f = os.path.join(*args)
    if not os.path.exists(f):
        raise Exception("path does not exist: " + f + ". Current dir=" + os.getcwd())
    return f

def run(arglist, noecho=False):
    if not noecho: print("running command:", " ".join(arglist))
    subprocess.check_call(arglist)

def run_and_capture_output(arglist, output_as_bytes_string=False, noecho=False):
    if not noecho: print("running command:", " ".join(arglist))
    out = subprocess.check_output(arglist)
    if not output_as_bytes_string:
        out = str(out, 'utf-8')
    return out

def ctor(class_, args):
    if not isinstance(args, list):
        args = [ args ]
    l = []
    for i in args:
        l.append(class_(i))
    return l

#------------------------------------------------------------------------------
class cwd_back:
    """temporarily change into a directory inside a with block"""

    def __init__(self, dir):
        self.dir = dir

    def __enter__(self):
        self.old = os.getcwd()
        if self.old == self.dir:
            return
        print("Entering directory", self.dir, "(was in {})".format(self.old))
        chkf(self.dir)
        os.chdir(self.dir)

    def __exit__(self, exc_type, exc_value, traceback):
        if self.old == self.dir:
            return
        print("Returning to directory", self.old, "(currently in {})".format(self.dir))
        chkf(self.old)
        os.chdir(self.old)

#------------------------------------------------------------------------------
class BuildItem:

    def __init__(self, name):
        self.name = name
        self.preload = None

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def preload(self):
        "return the name of a script to populate the cmake cache, via -C"
        return self.preload

#------------------------------------------------------------------------------
class BuildType(BuildItem):
    """Specifies a build type, ie, one of Release, Debug, etc"""

    @staticmethod
    def default():
        return BuildType("Release")

#------------------------------------------------------------------------------
class System(BuildItem):
    """Specifies an operating system"""

    @staticmethod
    def default():
        "return the current operating system"
        return System.current()

    @staticmethod
    def current():
        if not hasattr(System, "_current"):
            if sys.platform == "linux" or sys.platform == "linux2":
                System._current = System("linux")
            elif sys.platform == "darwin":
                System._current = System("mac")
            elif sys.platform == "win32":
                System._current = System("windows")
            else:
                raise Exception("unknown system")
        return System._current

#------------------------------------------------------------------------------
class Architecture(BuildItem):
    """Specifies a processor architecture"""

    @staticmethod
    def default():
        "return the architecture of the current machine"
        return Architecture.current()

    @staticmethod
    def current():
        # http://stackoverflow.com/a/12578715/5875572
        import platform
        machine = platform.machine()
        if machine.endswith('64'):
            return Architecture('x64')
        elif machine.endswith('86'):
            return Architecture('x32')
        raise Exception("unknown architecture")

#------------------------------------------------------------------------------
class CompileOptions:

    def __init__(self, name=""):
        self.name = name
        self.cmake_flags = []
        self.cflags = []
        self.lflags = []
        self.macros = []

#------------------------------------------------------------------------------
class Compiler(BuildItem):
    """Specifies a compiler"""

    @staticmethod
    def default():
        cpp = choose_executable("C++ compiler", os.environ.get('CXX'), 'c++', 'g++', 'clang++', 'icpc')
        return Compiler(cpp)

    def __init__(self, path):
        p = which(path)
        if p is None:
            raise Exception("compiler not found: " + path)
        if p != path:
            print("compiler: selected {} for {}".format(p, path))
        path = os.path.abspath(p)
        name = os.path.basename(path)
        in_path = path
        in_name = name
        #print("cmp: found compiler:", name, path)
        out = run_and_capture_output([path, '--version'], noecho=True).strip("\n")
        firstline = out.split("\n")[0]
        splits = firstline.split(" ")
        name = splits[0].lower()
        #print("cmp: version:", name, "---", firstline, "---")
        vregex = r'(\d+\.\d+)\.\d+'
        if name.startswith("g++") or name.startswith("gcc"):
            name = "gcc"
            version = run_and_capture_output([path, '-dumpversion'], noecho=True).strip("\n")
            version = re.sub(vregex, r'\1', version)
            #print("gcc version:", version, "---")
        elif name.startswith("clang"):
            name = "clang"
            version = re.sub(r'clang version ' + vregex + '.*', r'\1', firstline)
            #print("clang version:", version, "---")
        elif name.startswith("icpc"):
            name = "icc"
            version = re.sub(r'icpc \(ICC\) ' + vregex + '.*', r'\1', firstline)
            #print("icc version:", version, "---")
        else:
            version = run_and_capture_output([path, '--dumpversion'], noecho=True).strip("\n")
            version = re.sub(vregex, r'\1', version)
        #
        self.shortname = name
        self.gcclike = self.shortname in ('gcc', 'clang', 'icc')
        self.is_msvc = self.shortname.startswith('msvc')
        name += version
        self.path = path
        self.version = version
        self.version_full = firstline
        self.options = CompileOptions()
        super().__init__(name)
        if in_name.endswith("c++"):
            self.c_compiler = re.sub(r'c\+\+', r'cc', self.path)
        elif self.shortname == "icc":
            self.c_compiler = re.sub(r'icpc', r'icc', self.path)
        elif self.shortname == "gcc":
            self.c_compiler = re.sub(r'g\+\+', r'gcc', self.path)
        elif self.shortname == "clang":
            self.c_compiler = re.sub(r'clang\+\+', r'clang', self.path)
        else:
            self.c_compiler = self.path

    def wall(self, yes=True):
        if self.gcclike:
            if yes: self._f('-Wall')
        else:
            raise Exception("not implemented")

    def pedantic(self, yes=True):
        if self.gcclike:
            if yes: self._f('-Wpedantic')
        else:
            raise Exception("not implemented")

    def g3(self, yes=True):
        if self.gcclike:
            if yes: self._f('-g3')
        else:
            raise Exception("not implemented")

    def cpp11(self, yes=True):
        if self.gcclike:
            if yes: self._f('-std=c++11')
        else:
            raise Exception("not implemented")

    def cpp14(self, yes=True):
        if self.gcclike:
            if yes: self._f('-std=c++14')
        else:
            raise Exception("not implemented")

    def cpp1z(self, yes=True):
        if self.gcclike:
            if yes: self._f('-std=c++1z')
        else:
            raise Exception("not implemented")

    def no_strict_aliasing(self, yes=True):
        if self.gcclike:
            if yes: self._f('-fno-strict-aliasing')
        else:
            raise Exception("not implemented")

    def strict_aliasing(self, yes=True):
        if self.gcclike:
            if yes: self._f('-fstrict-aliasing')
        else:
            raise Exception("not implemented")

    def no_rtti(self, yes=True):
        if self.gcclike:
            if yes: self._f('-fno-rtti')
        else:
            raise Exception("not implemented")

    def no_exceptions(self, yes=True):
        if self.gcclike:
            if yes: self._f('-fno-exceptions', '-fno-unwind-tables')
        else:
            raise Exception("not implemented")

    def no_stdlib(self, yes=True):
        if self.gcclike:
            if yes: self._f('-nostdlib')
        else:
            raise Exception("not implemented")

    def pthread(self, yes=True):
        if self.gcclike:
            if yes: self._f('-pthread')
        else:
            raise Exception("not implemented")

    def _m(self, *macros):
        for m in macros:
            self.options.macros.append(m)
        
    def _l(self, *linkerflags):
        for f in flags:
            self.options.lflags.append(f)

    def _m(self, *macros):
        for m in macros:
            self.options.macros.append(m)

    options_map = {
        "wall":wall,
        "pedantic":pedantic,
        "g3":g3,
        "cpp11":cpp11,
        "cpp14":cpp14,
        "cpp1z":cpp1z,
        "no_strict_aliasing":no_strict_aliasing,
        "strict_aliasing":strict_aliasing,
        "no_rtti":no_rtti,
        "no_exceptions":no_exceptions,
        "no_stdlib":no_stdlib,
        "pthread":pthread,
    }

#------------------------------------------------------------------------------
class Variant(BuildItem):
    """for variations in compile options"""

    def __init__(self, name):
        super().__init__(name)
        self.options = CompileOptions()

#------------------------------------------------------------------------------
class Generator(BuildItem):
    """
    generators: https://cmake.org/cmake/help/v3.7/manual/cmake-generators.7.html

    Unix Makefiles
    Ninja
    Watcom WMake
    CodeBlocks - Ninja
    CodeBlocks - Unix Makefiles
    CodeLite - Ninja
    CodeLite - Unix Makefiles
    Eclipse CDT4 - Ninja
    Eclipse CDT4 - Unix Makefiles
    KDevelop3
    KDevelop3 - Unix Makefiles
    Kate - Ninja
    Kate - Unix Makefiles
    Sublime Text 2 - Ninja
    Sublime Text 2 - Unix Makefiles

    Visual Studio 6
    Visual Studio 7
    Visual Studio 7 .NET 2003
    Visual Studio 8 2005
    Visual Studio 9 2008
    Visual Studio 10 2010
    Visual Studio 11 2012
    Visual Studio 12 2013
    Visual Studio 14 2015
    Visual Studio 15 2017

    Green Hills MULTI
    Xcode
    """

    def __init__(self, name, num_jobs):
        super().__init__(name)
        self.num_jobs = num_jobs
        self.is_msvc = name.startswith("Visual Studio")
        self.is_makefile = name.endswith("Makefiles")
        self.is_ninja = name.endswith("Ninja")

    def compile_flags(self):
        if self.is_msvc:
            return ['/MP', self.num_jobs]
        else:
            return []

    def configure_args(self):
        if name != "":
            return ['-G', name]
        else:
            return []

    def cmd(self, targets):
        if self.is_makefile:
            return ['make', '-j', str(self.num_jobs)] + targets
        else:
            return ['cmake', '--build', '.', '--'] + targets

#------------------------------------------------------------------------------
class Build:
    """Holds a build's settings"""

    pfile = "pycmake_preload.cmake"

    def __init__(self, proj_root, build_root, install_root,
                 sys, arch, buildtype, compiler, variant,
                 generator):
        self.system = sys
        self.architecture = arch
        self.buildtype = buildtype
        self.compiler = compiler
        self.variant = variant
        self.crosscompile = (sys != System.current())
        self.toolchain = None
        self.dir = self._cat("-")
        self.projdir = chkf(proj_root)
        self.buildroot = os.path.abspath(build_root)
        self.builddir = os.path.abspath(os.path.join(build_root, self.dir))
        self.preload_file = os.path.join(self.builddir, Build.pfile)
        self.installroot = os.path.abspath(install_root)
        self.installdir = os.path.join(self.installroot, self.dir)
        self.generator = generator

    def __repr__(self):
        return self._cat("-")

    def _cat(self, sep):
        s = "{1}{0}{2}{0}{3}{0}{4}"
        s = s.format(sep, self.system, self.architecture, self.compiler, self.buildtype)
        if self.variant:
            s += "{0}{1}".format(sep, self.variant)
        return s

    def create_dir(self):
        if not os.path.exists(self.builddir):
            os.makedirs(self.builddir)

    def _gather_flags(self):
        flags = self.generator.compile_flags()
        return flags

    def create_preload_file(self):
        self.create_dir()
        lines = []
        def a(s): lines.append(s)
        def s(var, value):
            # http://stackoverflow.com/questions/17597673/cmake-preload-script-for-cache
            lines.append('set({} {} CACHE PATH "")'.format(var, value))
            lines.append('_pycmakedbg({})'.format(var))
            lines.append('')

        s("CMAKE_CXX_COMPILER", self.compiler.path)
        s("CMAKE_C_COMPILER", self.compiler.c_compiler)
        s("CMAKE_INSTALL_PREFIX", self.installdir)
        s("CMAKE_BUILD_TYPE", self.buildtype)
        flags = self._gather_flags()
        if flags:
            s('CMAKE_CXX_FLAGS', "\n".join(flags))

        if len(lines) > 0:
            l1 = "# Do not edit. Will be overwritten."
            l2 = "# Generated by pycmake on " + datetime.now().strftime("%Y/%m/%d %H:%m")
            lines.insert(0, l1)
            lines.insert(1, l2)
            lines.insert(2, "")
            lines.insert(3, 'message(STATUS "pycmake:preload----------------------")')
            lines.insert(4, """function(_pycmakedbg var)
message(STATUS "pycmake: ${var}=${${var}}")
endfunction(_pycmakedbg)
""")
            a('message(STATUS "pycmake:preload----------------------")')
            a("")
            a(l1)
            a(l2)
        with open(self.preload_file, "w") as f:
            f.writelines([l+"\n" for l in lines])
        return self.preload_file

    def configure(self):
        self.create_dir()
        if not os.path.exists(self.preload_file):
            self.create_preload_file()
        with cwd_back(self.builddir):
            cmd = (['cmake', '-C', os.path.basename(self.preload_file),]
                   + self.generator.configure_args() +
                   [#'-DCMAKE_TOOLCHAIN_FILE='+toolchain_file,
                   self.projdir])
            run(cmd)
            with open("pycmake_configure.done", "w") as f:
                f.write(" ".join(cmd) + "\n")

    def build(self, targets = []):
        self.create_dir()
        with cwd_back(self.builddir):
            if not os.path.exists("pycmake_configure.done"):
                self.configure()
            cmd = self.generator.cmd(targets)
            run(cmd)
            with open("pycmake_build.done", "w") as f:
                f.write(" ".join(cmd) + "\n")

    def install(self):
        self.create_dir()
        with cwd_back(self.builddir):
            if not os.path.exists("pycmake_build.done"):
                self.build()
            cmd = self.generator.cmd(['install'])
            run(cmd)

    def clean(self):
        self.create_dir()
        with cwd_back(self.builddir):
            cmd = self.generator.cmd(['clean'])
            run(cmd)
            os.remove("pycmake_build.done")

#------------------------------------------------------------------------------
class ProjectConfig:

    @staticmethod
    def default_systems():
        return ctor(System, ["linux", "windows", "android", "ios", "ps4", "xboxone"])
    @staticmethod
    def default_architectures():
        return ctor(Architecture, ["x86", "x64", "arm"])
    @staticmethod
    def default_buildtypes():
        return ctor(BuildType, ["Debug", "Release"])
    @staticmethod
    def default_compilers():
        return ctor(Compiler, ["clang++", "g++", "icpc"])
    # no default variants

    def __init__(self, **kwargs):
        projdir = kwargs.get('proj_dir', os.getcwd())
        if projdir == ".":
            projdir = os.getcwd()
        self.rootdir = projdir
        self.cmakelists = chkf(self.rootdir, "CMakeLists.txt")
        self.builddir = kwargs.get('build_dir', os.path.join(os.getcwd(), "build"))
        self.installdir = kwargs.get('install_dir', os.path.join(os.getcwd(), "install"))

        self.generator = Generator(kwargs.get('generator'), kwargs.get('jobs'))

        def _get(name, class_):
            g = kwargs.get(name)
            if g is None:
                g = [class_.default()] if class_ is not None else [None]
                return g
            l = []
            for i in g:
                l.append(class_(i))
            #print(name, ".....", g)
            return l
        self.systems = _get('systems', System)
        self.architectures = _get('architectures', Architecture)
        self.buildtypes = _get('build_types', BuildType)
        self.compilers = _get('compilers', Compiler)
        self.variants = _get('variants', None)

        configfile = os.path.join(projdir, "pycmake.json")
        self.configfile = None
        if os.path.exists(configfile):
            self.parse_file(configfile)
            self.configfile = configfile

        self.builds = []
        def _cbm(li):
            d = odict()
            for i in li:
                d[i] = []
            return d
        self.system_builds = _cbm(self.systems)
        self.architecture_builds = _cbm(self.architectures)
        self.buildtype_builds = _cbm(self.buildtypes)
        self.compiler_builds = _cbm(self.compilers)
        self.variant_builds = _cbm(self.variants)
        for s in self.systems:
            for a in self.architectures:
                for c in self.compilers:
                    for m in self.buildtypes:
                        for v in self.variants:
                            self.add_build_if_valid(s, a, m, c, v)

    def parse_file(self, configfile):
        raise Exception("not implemented")

    def add_build_if_valid(self, sys, arch, buildtype, compiler, variant):
        if not self.is_valid(sys, arch, buildtype, compiler, variant):
            return False
        b = Build(self.rootdir, self.builddir, self.installdir,
                  sys, arch, buildtype, compiler, variant,
                  self.generator)
        self.builds.append(b)
        #print(self.system_builds)
        self.system_builds[sys].append(b)
        self.architecture_builds[arch].append(b)
        self.buildtype_builds[buildtype].append(b)
        self.compiler_builds[compiler].append(b)
        self.variant_builds[variant].append(b)
        return True

    def is_valid(self, sys, arch, mode, compiler, variant):
        # TODO
        return True

    def select(self, **kwargs):
        out = [ b for b in self.builds ]
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

    def select_and_show(self, **kwargs):
        builds = self.select(**kwargs)
        if len(builds) > 0:
            print("selected builds:")
            for b in builds:
                print(b)
        else:
            print("no builds selected")
        return builds

    def show_builds(self, **kwargs):
        self.select_and_show(**kwargs)

    def create_tree(self, **restrict_to):
        builds = self.select_and_show(**restrict_to)
        for b in builds:
            d = b.create_dir()
            b.create_preload_file()
            #print(b, ":", d)

    def configure(self, **restrict_to):
        if not os.path.exists(self.builddir):
            os.makedirs(self.builddir)
        self._execute(Build.configure, "Configuring", **restrict_to)

    def build(self, **restrict_to):
        self._execute(Build.build, "Building", **restrict_to)

    def clean(self, **restrict_to):
        self._execute(Build.clean, "Cleaning", **restrict_to)

    def install(self, **restrict_to):
        self._execute(Build.install, "Installing", **restrict_to)

    def _execute(self, fn, msg, **restrict_to):
        builds = self.select_and_show(**restrict_to)
        if len(builds) == 0:
            return
        print("")
        print("===============================================")
        print(msg, ": start")
        for b in builds:
            print("-----------------------------------------------")
            print(msg, ":", b)
            print("-----------------------------------------------")
            fn(b)
        print("-----------------------------------------------")
        print(msg, ": finished")
        print("===============================================")

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def handle_args(in_args):
    from argparse import ArgumentParser,RawDescriptionHelpFormatter as HelpFormatter

    def argwip(h):
        return argparse.SUPPRESS

    # to update the examples in a Markdown file, pipe the help through
    # sed 's:^#\ ::g' | sed 's:^\$\(\ .*\):\n```\n$ \1\n```:g'
    parser = ArgumentParser(description='Handle several cmake build trees of a single project',
                            usage="""%(prog)s [-c,--configure] [-b,--build] [-i,--install] [options...] [proj-dir]""",
                            epilog="""
-----------------------------
Some examples:

# Configure and build a CMakeLists.txt project located on the dir above.
# The build trees will be placed under a folder "build" located on the
# current dir. Likewise, installation will be set to a sister dir
# named "install". A c++ compiler will be selected from the path, and the
# CMAKE_BUILD_TYPE will be set to Release.
$ %(prog)s -b ..

# Same as above, but now look for CMakeLists.txt on the current dir.
$ %(prog)s -b .

# Same as above.
$ %(prog)s -b

# Same as above, and additionally install.
$ %(prog)s -i

# Build both Debug and Release build types (resulting in 2 build trees).
$ %(prog)s -t Debug,Release

# Build using both clang++ and g++ (2 build trees).
$ %(prog)s -p clang++,g++

# Build using both clang++,g++ and in Debug,Release modes (4 build trees).
$ %(prog)s -p clang++,g++ -t Debug,Release

# Build using clang++,g++,icpc in Debug,Release,MinSizeRel modes (9 build trees).
$ %(prog)s -p clang++,g++,icpc -t Debug,Release,MinSizeRel
""",
                            formatter_class=HelpFormatter)

    parser.add_argument("proj-dir", nargs="?", default=".",
                        help="the directory where CMakeLists.txt is located (defaults to the current directory ie, \".\"). Passing a directory which does not contain a CMakeLists.txt will cause an exception.")

    cmds = parser.add_argument_group(title="Available commands")
    cmds.add_argument("-c", "--configure", action="store_true", default=False,
                      help="only configure the selected builds")
    cmds.add_argument("-b", "--build", action="store_true", default=False,
                      help="build the selected builds, configuring before if necessary")
    cmds.add_argument("-i", "--install", action="store_true", default=False,
                      help="install the selected builds, configuring and building before if necessary")
    cmds.add_argument("--clean", action="store_true", default=False,
                      help="clean the selected builds")
    cmds.add_argument("--create-tree", action="store_true", default=False,
                      help="just create the build tree and the cmake preload scripts")

    clo = parser.add_argument_group(title="Selecting the builds")
    clo.add_argument("-s", "--systems", metavar="os1,os2,...",
                     help="(WIP) restrict actions to the given operating systems. This feature requires os-specific toolchains and is currently a WIP.")
    clo.add_argument("-a", "--architectures", metavar="arch1,arch2,...",
                     help="(WIP) restrict actions to the given processor architectures")
    clo.add_argument("-p", "--compilers", metavar="compiler1,compiler2,...",
                     help="restrict actions to the given compilers")
    clo.add_argument("-t", "--build-types", metavar="type1,type2,...",
                     help="restrict actions to the given build types (eg Release or Debug)")
    clo.add_argument("-v", "--variants", metavar="variant1,variant2,...",
                     help="(WIP) restrict actions to the given variants")

    parser.add_argument("--build-dir", default="./build",
                        help="set the build root (defaults to ./build)")
    parser.add_argument("--install-dir", default="./install",
                        help="set the install root (defaults to ./install)")
    parser.add_argument("-G", "--generator", default="",
                        help="set the cmake generator")
    parser.add_argument("-j", "--jobs", default=str(cpu_count()),
                        help="""build with the given number of parallel jobs
                        (defaults to %(default)s on this machine).
                        This may not work with every generator.""")

    cli = parser.add_argument_group(title='Commands that show info')
    cli.add_argument("--show-builds", action="store_true", default=False,
                    help="")
    cli.add_argument("--show-systems", action="store_true", default=False,
                    help="")
    cli.add_argument("--show-architectures", action="store_true", default=False,
                    help="")
    cli.add_argument("--show-build-types", action="store_true", default=False,
                    help="")
    cli.add_argument("--show-compilers", action="store_true", default=False,
                    help="")
    cli.add_argument("--show-variants", action="store_true", default=False,
                    help="")

    ns = parser.parse_args(in_args[1:])
    #print(ns)
    # fix comma-separated lists
    for i in ('systems','architectures','build_types','compilers','variants'):
        a = getattr(ns, i)
        if a is not None:
            a = a.split(",")
            setattr(ns, i, a)

    return ns

#------------------------------------------------------------------------------

if __name__ == "__main__":

    #print(sys.argv)
    args = handle_args(sys.argv)
    #print(args)

    proj = ProjectConfig(**vars(args))

    if args.show_systems:
        for b in proj.systems:
            print(b)

    if args.show_architectures:
        for b in proj.architectures:
            print(b)

    if args.show_build_types:
        for b in proj.build_types:
            print(b)

    if args.show_compilers:
        for b in proj.compilers:
            print(b)

    if args.show_variants:
        for b in proj.variants:
            print(b)

    if args.show_builds:
        proj.show_builds()

    if args.create_tree:
        proj.create_tree()

    if args.configure:
        proj.configure()

    if args.build:
        proj.build()

    if args.install:
        proj.install()

    if args.clean:
        proj.clean()

