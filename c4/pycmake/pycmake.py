#!/usr/bin/env python3

import os
import subprocess
import sys
import re
import glob
import json
from datetime import datetime as datetime
from collections import OrderedDict as odict
from multiprocessing import cpu_count as cpu_count

PYCMAKE_DIR = os.path.expanduser("~/.pycmake/")
def open_file(name, access="r"):
    if not os.path.exists(PYCMAKE_DIR):
        os.makedirs(PYCMAKE_DIR)
    p = os.path.join(PYCMAKE_DIR, name)
    f = open(p, access)
    return f

def which(cmd):
    if os.path.exists(cmd):
        return cmd
    for path in os.environ["PATH"].split(os.pathsep):
        j = os.path.join(path, cmd)
        if os.path.exists(j):
                return j
    return None      

def find_executable(name):
    sufs = [""] if System.current_str() != "windows" else ["",".exe",".bat"]
    for s in sufs:
        n = name + s
        w = which(n)
        if w is not None:
            return w
    return None

def chkf(*args):
    "join the args as a path and check whether that path exists"
    f = os.path.join(*args)
    if not os.path.exists(f):
        raise Exception("path does not exist: " + f + ". Current dir=" + os.getcwd())
    return f

def run(arglist, noecho=False):
    s = " ".join(arglist)
    if not noecho: print("running command:", " ".join(arglist))
    try:
        subprocess.check_call(s)
    except:
        print("error running command: '{}'".format(s))
        raise

def run_and_capture_output(arglist, as_bytes_string=False, noecho=False):
    s = " ".join(arglist)
    if not noecho: print("running command:", s)
    if as_bytes_string:
        result = subprocess.run(s, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        result = subprocess.run(s, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                universal_newlines=True)
    try:
        result.check_returncode()
    except:
        print("error running command: '{}'".format(s))
        raise
    out = result.stdout
    return out

def cmember(obj, name, function):
    """add and cache an object member which is the result of a given function.
    This is useful for implementing lazy getters when the function call is expensive."""
    if hasattr(obj, name):
        val = getattr(obj, name)
    else:
        val = function()
        setattr(obj, name, val)
    return val

def ctor(cls, args):
    if not isinstance(args, list):
        args = [ args ]
    l = []
    for i in args:
        l.append(cls(i))
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

class CMakeSystemInformation:
    """encapsulates the results returned from `cmake [-G <which_generator>] --system-information`.
    This is used for selecting default values for system, compiler, generator, etc."""

    @staticmethod
    def generator():
        return cmember(__class__, '_generator',
                      lambda: __class__._getstr('CMAKE_GENERATOR', 'default'))

    @staticmethod
    def system_name(which_generator = "default"):
        return cmember(__class__, '_system_name',
                       lambda: __class__._getstr('CMAKE_SYSTEM_NAME', which_generator).lower())

    @staticmethod
    def architecture(which_generator = "default"):
        return cmember(__class__, '_architecture',
                       lambda: __class__._getstr('CMAKE_SYSTEM_PROCESSOR', which_generator).lower())

    @staticmethod
    def cxx_compiler(which_generator = "default"):
       return cmember(__class__, '_cxx_compiler',
                      lambda: __class__._getpath('CMAKE_CXX_COMPILER', which_generator))

    @staticmethod
    def c_compiler(which_generator = "default"):
        return cmember(__class__, '_c_compiler',
                      lambda: __class__._getpath('CMAKE_C_COMPILER', which_generator))

    @staticmethod
    def info(which_generator = "default"):
        return cmember(__class__, '_info'+which_generator, lambda: __class__.system_info(which_generator))

    @staticmethod
    def _getpath(var_name, which_generator):
        s = __class__._getstr(var_name, which_generator)
        #s = re.sub(r'\\', '/', s)
        return s

    @staticmethod
    def _getstr(var_name, which_generator):
        regex = r'^' + var_name + r' "(.*)"'
        for l in __class__.info(which_generator):
            if l.startswith(var_name):
                l = l.strip("\n").lstrip(" ").rstrip(" ")
                #print(var_name, "startswith :", l)
                if re.match(regex, l):
                    s = re.sub(regex, r'\1', l)
                    #print(var_name, "result: '" + s + "'")
                    return s
        err = "could not find variable {} in the output of `cmake --system-information`"
        raise Exception(err.format(var_name))

    @staticmethod
    def system_info(which_generator):
        p = re.sub(r'[() ]', '', which_generator)
        p = os.path.join(PYCMAKE_DIR, "info-"+which_generator)
        if os.path.exists(p):
            with open(p, "r") as f:
                i = f.readlines()
        else:
            if which_generator == "default":
                cmd = ['cmake', '--system-information']
            else:
                which_generator = VisualStudioInfo.name_to_gen(which_generator)
                gen = '"{}"'.format(which_generator)
                cmd = ['cmake', '-G', gen, '--system-information']
            if not os.path.exists(PYCMAKE_DIR):
                os.makedirs(PYCMAKE_DIR)
            with cwd_back(PYCMAKE_DIR):
                out = run_and_capture_output(cmd, noecho=True)
            with open(p, "w") as f:
                f.write(out)
            i = out.split("\n")
        return i

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
    def current():
        "return the current operating system"
        return System(__class__.current_str())

    @staticmethod
    def current_str():
        s = CMakeSystemInformation.system_name()
        if s == "mac os x" or s == "Darwin":
            s = "mac"
        return s
        #if not hasattr(System, "_current"):
        #    if sys.platform == "linux" or sys.platform == "linux2":
        #        System._current = System("linux")
        #    elif sys.platform == "darwin":
        #        System._current = System("mac")
        #    elif sys.platform == "win32":
        #        System._current = System("windows")
        #    else:
        #        raise Exception("unknown system")
        #return System._current
        
#------------------------------------------------------------------------------
class Architecture(BuildItem):
    """Specifies a processor architecture"""

    @staticmethod
    def current():
        "return the architecture of the current machine"
        return Architecture(__class__.current_str())

    @staticmethod
    def current_str():
        s = CMakeSystemInformation.architecture()
        if s == "amd64":
            s = "x86_64"
        return s
        ## http://stackoverflow.com/a/12578715/5875572
        #import platform
        #machine = platform.machine()
        #if machine.endswith('64'):
        #    return Architecture('x86_64')
        #elif machine.endswith('86'):
        #    return Architecture('x32')
        #raise Exception("unknown architecture")

    @property
    def is64(self):
        def fn():
            s = re.search('64', self.name)
            return (s != None)
        return cmember(self, "_is64", fn)

    @property
    def is32(self):
        return not self.is64

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
    def current():
        return Compiler(__class__.current_str())

    @staticmethod
    def current_str():
        if str(System.current()) != "windows":
            cpp = CMakeSystemInformation.cxx_compiler()
        else:
            vs = find_visual_studio()
            if vs is None:
                cpp = CMakeSystemInformation.cxx_compiler()
            else:
                generator = Generator.resolve_alias(vs)
                cpp = CMakeSystemInformation.cxx_compiler(generator)
        return cpp
        
    def __init__(self, path):
        if path.startswith("vs"):
            path = __class__.resolve_vs(path)
            self.explicit = False
        else:
            self.explicit = True
        p = which(path)
        if p is None:
            raise Exception("compiler not found: " + path)
        if p != path:
            print("compiler: selected {} for {}".format(p, path))
        path = os.path.abspath(path)
        name = os.path.basename(path)
        in_path = path
        in_name = name
        name,version,version_full = self.get_version(path)
        self.shortname = name
        self.gcclike = self.shortname in ('gcc', 'clang', 'icc')
        self.is_msvc = self.shortname.startswith('vs')
        name += version
        self.path = path
        self.version = version
        self.version_full = version_full
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
        if self.is_msvc:
            self.msbuild = __class__.resolve_msbuild(self.name)

    def get_version(self, path):

        # is this visual studio?
        if re.search('Visual Studio', path):
            out = run_and_capture_output([path], noecho=True).strip("\n")
            #print("out", out)
            version_full = out.split("\n")[0]
            #print("version_full", version_full)
            name = "vs"
            if re.search('Visual Studio 13', path):
                version = "2013"
            elif re.search('Visual Studio 14', path):
                version = "2015"
            elif re.search('Visual Studio 15', path):
                version = "2017"
            else:
                raise Exception("not implemented")
            return name,version,version_full

        # other compilers
        #print("cmp: found compiler:", name, path)
        out = run_and_capture_output([path, '--version'], noecho=True).strip("\n")
        version_full = out.split("\n")[0]
        splits = version_full.split(" ")
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
        return name,version,version_full

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

    @staticmethod
    def resolve_vs(name):
        assert name.startswith("vs")
        return CMakeSystemInformation.cxx_compiler(name)

#------------------------------------------------------------------------------
class VisualStudioInfo:

    # an enumeration of known VS versions, set in order of preference
    _versions = odict([
        ('vs2015', 14),
        ('vs2017', 15),
        ('vs2013', 12),
        ('vs2012', 11),
        ('vs2010', 10),
        ('vs2008', 9),
        ('vs2005', 8),
    ])

    def __init__(self, name):
        if not name in __class__._versions.keys():
            raise Exception("unknown alias")
        ver = __class__._versions[name]
        self.name = name
        self.ver = ver
        self.year = int(re.sub(r'^vs', '', name))
        self.gen = __class__.name_to_gen(name)
        self.dir = __class__.vsdir(ver)
        self.msbuild = __class__.msbuild(ver)
        self.vcvarsall = __class__.vcvarsall(ver)
        self.is_installed = __class__.is_installed(ver)

    def check(self):
        pass

    def cmd(self, args):
        if isinstance(args, list):
            args = " ".join(args)
        args = self.vcvarsall + "; " + args
        raise Exception("TODO")

    @staticmethod
    def find_any():
        for k,v in __class__._versions.items():
            if __class__.is_installed(v):
                return __class__(k)
        return None

    @staticmethod
    def name_to_gen(name_or_gen):
        if name_or_gen.startswith('Visual Studio '):
            return name_or_gen
        else:
            a = __class__._versions.get(name_or_gen)
            if a is None:
                raise Exception("unknown Visual Studio alias: " + name_or_gen)
            a = "Visual Studio " + str(a) + " " + re.sub(r'^vs', '', name_or_gen)
        return a

    @staticmethod
    def vsdir(ver):
        "get the directory where VS is installed"
        if ver < 15:
            progfilesx86 = os.environ['ProgramFiles(x86)']
            d = os.path.join(progfilesx86, 'Microsoft Visual Studio ' + str(ver) + '.0')
        elif ver == 15:
            # VS 2017+ is no longer a singleton, and may be installed anywhere,
            # so use CMake to do the grunt work for us, and pick up from there.
            # http://stackoverflow.com/questions/40694598/how-do-i-call-visual-studio-2017-rcs-version-of-msbuild-from-a-bat-files
            def fn():
                if not __class__.is_installed(ver): # but use cmake only if VS2017 is installed
                    return ""
                gen = 'Visual Studio 15 2017'
                if Architecture.current().is64:
                    gen += ' Win64'
                cxx = CMakeSystemInformation.cxx_compiler(gen)
                # VC dir is located on the root of the VS install dir
                vsdir = re.sub(r'(.*)[\\/]VC[\\/].*', r'\1', str(cxx))
                return vsdir
            d = cmember(__class__, '_vs2017dir', fn)
        else:
            raise Exception('VS Version not implemented: ' + str(ver))
        return d

    @staticmethod
    def vcvarsall(ver):
        "get the path to vcvarsall.bat"
        if ver < 15:
            s = os.path.join(__class__.vsdir(ver), 'VC', 'vcvarsall.bat')
        elif ver == 15:
            s = os.path.join(__class__.vsdir(ver), 'VC', 'Auxiliary', 'Build', 'vcvarsall.bat')
        else:
            raise Exception('VS Version not implemented: ' + str(ver))
        return s

    @staticmethod
    def msbuild(ver):
        "get the MSBuild.exe path"
        if ver < 15:
            progfilesx86 = os.environ['ProgramFiles(x86)']
            msbuild = os.path.join(progfilesx86, 'MSBuild', str(ver)+'.0', 'bin', 'MSBuild.exe')
        else:
            if ver > 15:
                raise Exception('VS Version not implemented: ' + str(ver))
            if Architecture.current().is64:
                msbuild = os.path.join(__class__.vsdir(ver), 'MSBuild', '15.0', 'Bin', 'amd64', 'MSBuild.exe')
            else:
                msbuild = os.path.join(__class__.vsdir(ver), 'MSBuild', '15.0', 'Bin', 'MSBuild.exe')
        return msbuild

    @staticmethod
    def is_installed(ver):
        if ver < 15:
            import winreg as wr
            key = "SOFTWARE\Microsoft\VisualStudio\{}.0"
            try:
                wr.OpenKey(wr.HKEY_LOCAL_MACHINE, key.format(ver), 0, wr.KEY_READ)
                # fail if we can't find the dir
                if not os.path.exists(__class__.vsdir(ver)):
                    return False
                if not os.path.exists(__class__.vcvarsall(ver)):
                    return False
                return True
            except:
                return False
        else:
            #
            # ~~~~~~~~~~~~~~ this is fragile.... ~~~~~~~~~~~~~~
            #
            # Unlike earlier versions, VS2017 is no longer a singleton installation.
            # Each VS2017 installed instance keeps a store of its data under
            # %ProgramData%\Microsoft\VisualStudio\Packages\_Instances\<hash>\state.json
            #
            # this info was taken from:
            # http://stackoverflow.com/questions/40694598/how-do-i-call-visual-studio-2017-rcs-version-of-msbuild-from-a-bat-files
            progdata = os.environ['ProgramData']
            instances_dir = os.path.join(progdata, 'Microsoft', 'VisualStudio', 'Packages', '_Instances')
            if not os.path.exists(instances_dir):
                return False
            pat = os.path.join(instances_dir, '*', 'state.json')
            instances = glob.glob(pat)
            if not instances:
                return False
            got_one = False
            for i in instances:
                with open(i, encoding="utf8") as json_str:
                    d = json.load(json_str)
                    def _get(*entry):
                        j = "/".join(list(entry))
                        try:
                            if isinstance(entry, str):
                                v = d[entry]
                            else:
                                v = None
                                for e in entry:
                                    #print("key:", e, "value:", v if v is not None else "<none yet>")
                                    v = v[e] if v is not None else d[e]
                        except:
                            raise Exception("could not find entry '" + j + "' in the json data at " + i + "\nMaybe the specs have changed?")
                        return v
                    # check that the version matches
                    version_string = _get('catalogInfo', 'buildVersion')
                    version_number = int(re.sub(r'(\d\d).*', r'\1', version_string))
                    if version_number != ver:
                        continue
                    # check that the directory exists
                    install_dir = _get('installationPath')
                    if not os.path.exists(install_dir):
                        continue
                    # maybe further checks are necessary?
                    # For now we stop here, and accept that this installation exists.
                    got_one = True
            return got_one

#------------------------------------------------------------------------------
class Variant(BuildItem):
    """for variations in compile options"""

    def __init__(self, name):
        super().__init__(name)
        self.options = CompileOptions()

#------------------------------------------------------------------------------
class Generator(BuildItem):

    """
    Visual Studio aliases example:
    vs2013: use the bitness of the current OS
    vs2013_32: use 32bit version
    vs2013_64: use 64bit version
    """

    @staticmethod
    def default():
        return Generator(__class__.default_str(), cpu_count())

    @staticmethod
    def default_str():
        s = CMakeSystemInformation.generator()
        return s

    def __init__(self, name_or_alias, num_jobs):
        name = Generator.resolve_alias(name_or_alias)
        self.alias = name_or_alias
        super().__init__(name)
        self.num_jobs = num_jobs
        self.is_makefile = name.endswith("Makefiles")
        self.is_ninja = name.endswith("Ninja")
        self.is_msvc = name.startswith("Visual Studio")

    def compile_flags(self):
        return []

    def configure_args(self):
        if self.name != "":
            return ['-G', '"{}"'.format(self.name)]
        else:
            return []

    def cmd(self, targets, compiler):
        if self.is_makefile:
            return ['make', '-j', str(self.num_jobs)] + targets
        elif self.is_msvc:
            if not hasattr(self, "sln"):
                sln = glob.glob("*.sln")
                if len(sln) != 1:
                    raise Exception("there's more than one solution file in the project folder")
                self.sln = sln[0]
            t = ['/t:'+str(t) for t in targets]
            return [compiler.msbuild, '/maxcpucount:'+self.num_jobs] + t + [self.sln]
        else:
            return ['cmake', '--build', '.', '--'] + targets

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

    @staticmethod
    def resolve_alias(alias):
        a = alias
        #
        if not alias.startswith("vs"):
            return a
        #
        if alias.startswith("vs2017"):
            a = 'Visual Studio 15 2017'
        elif alias.startswith("vs2015"):
            a = 'Visual Studio 14 2015'
        elif alias.startswith("vs2013"):
            a = 'Visual Studio 12 2013'
        elif alias.startswith("vs2012"):
            a = 'Visual Studio 11 2012'
        elif alias.startswith("vs2010"):
            a = 'Visual Studio 10 2010'
        elif alias.startswith("vs2008"):
            a = 'Visual Studio 09 2008'
        elif alias.startswith("vs2005"):
            a = 'Visual Studio 08 2005'
        else:
            raise Exception("unknown alias for visual studio: '{}'".format(alias))
        #
        if alias.endswith("_arm"):
            a += " ARM"
        elif alias.endswith("_ia64"):
            a += " IA64"
        elif alias.endswith("_32"):
            pass
        elif alias.endswith("_64"):
            a += " Win64"
        else:
            # no platform specified, so choose generator for the current platform
            if Architecture.current().is64:
                a += " Win64"
        return a

#------------------------------------------------------------------------------
class Build:
    """Holds a build's settings"""

    pfile = "pycmake_preload.cmake"

    def __init__(self, proj_root, build_root, install_root,
                 sys, arch, buildtype, compiler, variant,
                 generator):
        self.generator = generator
        self.system = sys
        self.architecture = arch
        self.buildtype = buildtype
        self.compiler = compiler
        self.variant = variant
        #self.crosscompile = (sys != System.current())
        #self.toolchain = None
        self.dir = self._cat("-")
        self.projdir = chkf(proj_root)
        self.buildroot = os.path.abspath(build_root)
        self.builddir = os.path.abspath(os.path.join(build_root, self.dir))
        self.preload_file = os.path.join(self.builddir, Build.pfile)
        self.installroot = os.path.abspath(install_root)
        self.installdir = os.path.join(self.installroot, self.dir)

    def __repr__(self):
        return self._cat("-")

    def _cat(self, sep):
        if self.compiler.is_msvc:
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
        flags = self.generator.compile_flags()
        return flags

    def create_preload_file(self):
        self.create_dir()
        lines = []
        # http://stackoverflow.com/questions/17597673/cmake-preload-script-for-cache
        def _s(var, value, type):
            lines.append('set({} {} CACHE {} "")'.format(var, '"{}"'.format(value), type))
            lines.append('_pycmakedbg({})'.format(var))
            lines.append('')
        def s(var, value): _s(var, value, "STRING")
        def p(var, value): _s(var, re.sub(r'\\', '/', value), "PATH")
        def f(var, value): _s(var, re.sub(r'\\', '/', value), "FILEPATH")

        f("CMAKE_CXX_COMPILER", self.compiler.path)
        f("CMAKE_C_COMPILER", self.compiler.c_compiler)
        p("CMAKE_INSTALL_PREFIX", self.installdir)
        s("CMAKE_BUILD_TYPE", self.buildtype)
        flags = self._gather_flags()
        if flags:
            s('CMAKE_CXX_FLAGS', " ".join(flags))

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
            lines.append('message(STATUS "pycmake:preload----------------------")')
            lines.append("")
            lines.append(l1)
            lines.append(l2)
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
            #if self.compiler.is_msvc and len(targets) == 0:
            #    targets = ["ALL_BUILD"]
            cmd = self.generator.cmd(targets, self.compiler)
            run(cmd)
            with open("pycmake_build.done", "w") as f:
                f.write(" ".join(cmd) + "\n")

    def install(self):
        self.create_dir()
        with cwd_back(self.builddir):
            if not os.path.exists("pycmake_build.done"):
                self.build()
            if self.compiler.is_msvc:
                targets = ["INSTALL"]
            else:
                targets = ["install"]
            cmd = self.generator.cmd(targets, self.compiler)
            run(cmd)

    def clean(self):
        self.create_dir()
        with cwd_back(self.builddir):
            cmd = self.generator.cmd(['clean'])
            run(cmd)
            os.remove("pycmake_build.done")

#------------------------------------------------------------------------------
class ProjectConfig:

    #@staticmethod
    #def default_systems():
    #    return ctor(System, ["linux", "windows", "android", "ios", "ps4", "xboxone"])
    #@staticmethod
    #def default_architectures():
    #    return ctor(Architecture, ["x86", "x86_64", "arm"])
    #@staticmethod
    #def default_buildtypes():
    #    return ctor(BuildType, ["Debug", "Release"])
    #@staticmethod
    #def default_compilers():
    #    return ctor(Compiler, ["clang++", "g++", "icpc"])
    ## no default variants

    def __init__(self, **kwargs):
        projdir = kwargs.get('proj_dir', os.getcwd())
        if projdir == ".":
            projdir = os.getcwd()
        self.rootdir = projdir
        self.cmakelists = chkf(self.rootdir, "CMakeLists.txt")
        self.builddir = kwargs.get('build_dir', os.path.join(os.getcwd(), "build"))
        self.installdir = kwargs.get('install_dir', os.path.join(os.getcwd(), "install"))

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

        self.generator = Generator(kwargs.get('generator'), kwargs.get('jobs'))

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
                            usage="""%(prog)s [-c,--configure] [-b,--build] [-i,--install] [more commands...] [options...] [proj-dir]""",
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
    clo.add_argument("-t", "--build-types", metavar="type1,type2,...", default="Release",
                     help="""restrict actions to the given build types.
                     Defaults to \"%(default)s\".""")
    clo.add_argument("-p", "--compilers", metavar="compiler1,compiler2,...",
                     default=str(Compiler.current_str()),
                     help="""restrict actions to the given compilers.
                     Defaults to CMake's default compiler, \"%(default)s\" on this system.""")
    clo.add_argument("-s", "--systems", metavar="os1,os2,...", default=str(System.current_str()),
                     help="""(WIP) restrict actions to the given operating systems.
                     Defaults to the current system, \"%(default)s\".
                     This feature requires os-specific toolchains and is currently a
                     work-in-progress.""")
    clo.add_argument("-a", "--architectures", metavar="arch1,arch2,...",
                     default=str(Architecture.current_str()),
                     help="""(WIP) restrict actions to the given processor architectures.
                     Defaults to CMake's default architecture, \"%(default)s\" on this system.
                     This feature requires os-specific toolchains and is currently a
                     work-in-progress.""")
    clo.add_argument("-v", "--variants", metavar="variant1,variant2,...",
                     help="""(WIP) restrict actions to the given variants.
                     This feature is currently a work-in-progress.""")

    parser.add_argument("--build-dir", default="./build",
                        help="set the build root (defaults to ./build)")
    parser.add_argument("--install-dir", default="./install",
                        help="set the install root (defaults to ./install)")
    parser.add_argument("-G", "--generator", default=str(Generator.default_str()),
                        help="set the cmake generator (on this machine, defaults to \"%(default)s\")")
    parser.add_argument("-j", "--jobs", default=str(cpu_count()),
                        help="""build with the given number of parallel jobs
                        (defaults to %(default)s on this machine).
                        This may not work with every generator.""")

    cli = parser.add_argument_group(title='Commands that show info')
    cli.add_argument("--show-args", action="store_true", default=False,
                     help="")
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

    arch = Architecture.current()
    for v in ("vs2017",):
        vs = Generator(v, cpu_count())
        print(v, "--->", vs.name)
        v32 = v + "_32" 
        vs = Generator(v32, cpu_count())
        print(v32, "--->", vs.name)
        v64 = v + "_64" 
        vs = Generator(v64, cpu_count())
        print(v64, "--->", vs.name)
        cxx = Compiler(v)
        print("compiler:", v, cxx.name)
    exit()

    #print(sys.argv)
    args = handle_args(sys.argv)
    #print(args)

    proj = ProjectConfig(**vars(args))

    if args.show_args:
        from pprint import pprint
        pprint(args)

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
