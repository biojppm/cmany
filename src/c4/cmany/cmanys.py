#!/usr/bin/env python3

import os
import re
import glob
import json
import copy
from datetime import datetime
from collections import OrderedDict as odict
from multiprocessing import cpu_count as cpu_count

from . import util
from .cmake import CMakeSysInfo, CMakeCache, getcachevars
from . import vsinfo
from . import flags as c4flags
from .conan import Conan

import argparse
from . import args as c4args


# -----------------------------------------------------------------------------
class NamedItem:

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


# -----------------------------------------------------------------------------
class BuildFlags(NamedItem):

    def __init__(self, name, compiler=None, **kwargs):
        super().__init__(name)
        self.cmake_vars = kwargs.get('vars', [])
        self.defines = kwargs.get('defines', [])
        self.cflags = kwargs.get('cflags', [])
        self.cxxflags = kwargs.get('cxxflags', [])
        # self.include_dirs = kwargs['include_dirs']
        # self.link_dirs = kwargs['link_dirs']
        if compiler is not None:
            self.resolve_flag_aliases(compiler)

    def resolve_flag_aliases(self, compiler):
        self.defines = c4flags.as_defines(self.defines, compiler)
        self.cflags = c4flags.as_flags(self.cflags, compiler)
        self.cxxflags = c4flags.as_flags(self.cxxflags, compiler)

    def append_flags(self, other, append_to_name=True):
        """other will take precedence, ie, their options will come last"""
        if append_to_name and other.name:
            self.name += '_' + other.name
        self.cmake_vars += other.cmake_vars
        self.defines += other.defines
        self.cflags += other.cflags
        self.cxxflags += other.cxxflags
        # self.include_dirs += other.include_dirs
        # self.link_dirs += other.link_dirs

    def log(self, log_fn=print, msg=""):
        t = "BuildFlags[{}]: {}".format(self.name, msg)
        log_fn(t, "cmake_vars=", self.cmake_vars)
        log_fn(t, "defines=", self.defines)
        log_fn(t, "cxxflags=", self.cxxflags)
        log_fn(t, "cflags=", self.cflags)

    @staticmethod
    def parse_specs(v):
        """in some cases the shell (or argparse?) removes quotes, so we need
        to parse flag specifications using regexes. This function implements
        this parsing for use in argparse. This one was a tough nut to crack."""
        # remove start and end quotes if there are any
        if util.is_quoted(v):
            v = util.unquote(v)
        # split at commas, but make sure those commas separate variants
        # (commas inside a variant spec are legitimate)
        vli = ['']    # the variant list
        rest = str(v) # the part of the variant specification yet to be read
        while True:
            # ... is there a smarter way to deal with the quotes?
            matches = re.search(__class__._rxdq, rest)  # try double quotes
            if matches is None:
                matches = re.search(__class__._rxsq, rest)  # try single quotes
                if matches is None:
                    matches = re.search(__class__._rxnq, rest)  # try no quotes
                    if matches is None:
                        if rest:
                            vli[-1] += rest
                        break
            (lhs, var, spec, rest) = matches.groups()
            if lhs:
                vli[-1] += lhs.strip(',')
            if var:
                if vli[-1]:
                    vli.append(var + spec)
                else:
                    vli[-1] += var + spec  # insert into empty specs
        # unquote split elements
        vli = [util.unquote(v).strip(',') for v in vli]
        return vli

    _rxdq = re.compile(r'(.*?)"([a-zA-Z0-9_]+?:)(.*?)"(.*)')  # double quotes
    _rxsq = re.compile(r"(.*?)'([a-zA-Z0-9_]+?:)(.*?)'(.*)")  # single quotes
    _rxnq = re.compile(r"(.*?)([a-zA-Z0-9_]+?:)(.*?)(.*)")    # no quotes


# -----------------------------------------------------------------------------
class BuildItem(NamedItem):
    """A base class for build items."""

    def __init__(self, name_or_spec):
        self.name = name_or_spec
        self.flags = BuildFlags(name_or_spec)
        self.full_specs = name_or_spec
        self.flag_specs = []
        #
        self.parse_specs(name_or_spec)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def parse_specs(self, spec):
        spec = util.unquote(spec)
        spl = spec.split(':')
        if len(spl) == 1:
            return
        name = spl[0]
        rest = spl[1]
        super().__init__(name)
        self.flag_specs = util.splitesc_quoted(rest, ' ')
        parser = argparse.ArgumentParser()
        c4args.add_cflags(parser)
        args = parser.parse_args(self.flag_specs)
        self.flags = BuildFlags(name, None, **vars(args))


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
            # if p != path:
            #     print("compiler: selected {} for {}".format(p, path))
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
        elif name.startswith("icpc") or name.startswith("icc"):
            name = "icc"
            version = re.sub(r'icpc \(ICC\) ' + vregex + '.*', r'\1', version_full)
            # print("icc version:", version, "---")
        else:
            version = slntout([path, '-dumpversion'])
            version = re.sub(vregex, r'\1', version)
        #
        return name, version, version_full

    def create_32bit_version(self, here):
        cxx = os.path.splitext(os.path.basename(self.path))[0]
        cc = os.path.splitext(os.path.basename(self.c_compiler))[0]
        if util.in_windows():
            cxxpath = os.path.join(here, cxx + "-32.bat")
            ccpath = os.path.join(here, cc + "-32.bat")
            fmt = """
@echo OFF
{path} {flag32} %*
exit /b %ERRORLEVEL%
"""
        else:
            cxxpath = os.path.join(here, cxx + "-32")
            ccpath = os.path.join(here, cc + "-32")
            fmt = """#!/bin/bash
{path} {flag32} $*
exit $?
"""
        if self.gcclike:
            for n in ((cxxpath, self.path), (ccpath, self.c_compiler)):
                txt = fmt.format(path=n[1], flag32='-m32')
                with open(n[0], 'w') as f:
                    f.write(txt)
                util.set_executable(n[0])
        result = Compiler(cxxpath)
        return result


# -----------------------------------------------------------------------------
class Variant(BuildFlags):
    """for variations in build flags"""

    @staticmethod
    def default():
        return Variant('none')

    @staticmethod
    def create(spec_list):
        if isinstance(spec_list, str):
            spec_list = util.splitesc_quoted(spec_list, ',')
        variants = []
        for s in spec_list:
            v = Variant(s)
            variants.append(v)
        for s in variants:
            s.resolve_references(variants)
        return variants

    def __init__(self, spec):
        self.full_specs = spec
        self.flag_specs = []
        self.refs = []
        self._resolved_references = False
        spec = util.unquote(spec)
        spl = spec.split(':')
        if len(spl) == 1:
            name = spec
            super().__init__(name)
            return
        name = spl[0]
        rest = spl[1]
        super().__init__(name)
        spl = util.splitesc_quoted(rest, ' ')
        curr = ""
        for s in spl:
            if s[0] != '@':
                curr += " " + s
            else:
                self.refs.append(s[1:])
                if curr:
                    self.flag_specs.append(curr)
                    curr = ""
                self.flag_specs.append(s)
        if curr:
            self.flag_specs.append(curr)

    def resolve_references(self, variants):
        if self._resolved_references:
            return
        def _find_variant(name):
            for v in variants:
                if v.name == name:
                    return v
            raise Exception("variant '{}' not found in {}".format(name, variants))
        for s_ in self.flag_specs:
            s = s_.lstrip()
            if s[0] == '@':
                refname = s[1:]
                r = _find_variant(refname)
                if self.name in r.refs:
                    msg = "circular reference found in variant definition: '{}'x'{}'"
                    raise Exception(msg.format(self.name, r.name))
                if not r._resolved_references:
                    r.resolve_all(variants)
                self.append_flags(r, append_to_name=False)
            else:
                parser = argparse.ArgumentParser()
                c4args.add_cflags(parser)
                ss = util.splitesc_quoted(s, ' ')
                args = parser.parse_args(ss)
                tmp = BuildFlags('', None, **vars(args))
                self.append_flags(tmp, append_to_name=False)
        self._resolved_references = True

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
        """create a generator"""
        if build.compiler.is_msvc:
            vsi = vsinfo.VisualStudioInfo(build.compiler.name)
            g = Generator(vsi.gen, build, num_jobs)
            build.adjust(architecture=Architecture(vsi.architecture))
            return g
        else:
            if build.architecture.is32:
                c = build.compiler.create_32bit_version(build.buildroot)
                build.adjust(compiler=c)
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
        self.sysinfo_name = self.name
        if self.is_msvc:
            ts = build.compiler.vs.toolset
            self.sysinfo_name += (' ' + ts) if ts is not None else ""
        # these vars would not change cmake --system-information
        # self.full_name += " ".join(self.build.flags.cmake_vars)

    def configure_args(self, for_json=False):
        if self.name != "":
            if self.is_msvc and self.build.compiler.vs.toolset is not None:
                if for_json:
                    args = '-T ' + self.build.compiler.vs.toolset
                else:
                    args = ['-G', self.name, '-T', self.build.compiler.vs.toolset]
            else:
                if for_json:
                    args = ''
                else:
                    args = ['-G', self.name]
        else:
            if for_json:
                args = ''
            else:
                args = []
        # cmake vars are explicitly set in the preload file
        # args += self.build.flags.cmake_flags
        return args

    def cmd(self, targets):
        if self.is_makefile:
            return ['make', '-j', str(self.num_jobs)] + targets
        else:
            bt = str(self.build.buildtype)
            if len(targets) > 1:
                msg = ("Building multiple targets with this generator is not implemented. "
                       "cmake --build cannot handle multiple --target " +
                       "invokations. A generator-specific command must be "
                       "written to handle multiple targets with this "
                       "generator " + '("{}")'.format(self.name))
                raise Exception(msg)
            if not self.is_msvc:
                cmd = ['cmake', '--build', '.', '--target', targets[0], '--config', bt]
            else:
                # if a target has a . in the name, it must be substituted for _
                targets_safe = [re.sub(r'\.', r'_', t) for t in targets]
                if len(targets_safe) != 1:
                    raise Exception("msbuild can only build one target at a time: was " + str(targets_safe))
                t = targets_safe[0]
                pat = os.path.join(self.build.builddir, t + '*.vcxproj')
                projs = glob.glob(pat)
                if len(projs) == 0:
                    msg = "could not find vcx project for this target: {} (glob={}, got={})".format(t, pat, projs)
                    raise Exception(msg)
                elif len(projs) > 1:
                    msg = "multiple vcx projects for this target: {} (glob={}, got={})".format(t, pat, projs)
                    raise Exception(msg)
                proj = projs[0]
                cmd = [self.build.compiler.vs.msbuild, proj,
                       '/property:Configuration='+bt,
                       '/maxcpucount:' + str(self.num_jobs)]
            return cmd

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
               num_jobs, kwargs):
        #
        self.kwargs = kwargs
        #
        self.projdir = util.chkf(proj_root)
        self.buildroot = os.path.abspath(build_root)
        self.installroot = os.path.abspath(install_root)
        #
        self.system = system
        self.architecture = arch
        self.buildtype = buildtype
        self.compiler = compiler
        self.variant = variant
        self.flags = flags
        # self.crosscompile = (system != System.default())
        # self.toolchain = None

        self.adjusted = False

        self._set_paths()
        # WATCHOUT: this may trigger a readjustment of this build's parameters
        self.generator = Generator.create(self, num_jobs)

        self.variant.resolve_flag_aliases(self.compiler)

        # This will load the vars from the builddir cache, if it exists.
        # It should be done only after creating the generator.
        self.varcache = CMakeCache(self.builddir)
        # ... and this will overwrite (in memory) the vars with the input
        # arguments. This will make the cache dirty and so we know when it
        # needs to be committed back to CMakeCache.txt
        self.gather_input_cache_vars()

        self.deps = kwargs.get('deps', '')
        if self.deps and not os.path.isabs(self.deps):
            self.deps = os.path.abspath(self.deps)
        self.deps_prefix = kwargs.get('deps_prefix')
        if not self.deps_prefix:
            self.deps_prefix = self.builddir

    def _set_paths(self):
        self.tag = self._cat('-')
        self.buildtag = self.tag
        self.installtag = self.tag  # this was different in the past and may become so in the future
        self.builddir = os.path.abspath(os.path.join(self.buildroot, self.buildtag))
        self.installdir = os.path.join(self.installroot, self.installtag)
        self.preload_file = os.path.join(self.builddir, Build.pfile)
        self.cachefile = os.path.join(self.builddir, 'CMakeCache.txt')

    def adjust(self, **kwargs):
        a = kwargs.get('architecture')
        if a and a != self.architecture:
            self.adjusted = True
            self.architecture = a
        c = kwargs.get('compiler')
        if c and c != self.compiler:
            self.adjusted = True
            self.compiler = c
        self._set_paths()

    def __repr__(self):
        return self.tag

    def _cat(self, sep):
        s = "{1}{0}{2}{0}{3}{0}{4}"
        s = s.format(sep, self.system, self.architecture, self.compiler, self.buildtype)
        if self.variant and self.variant.name and self.variant.name != "none":
            s += "{0}{1}".format(sep, self.variant)
        return s

    def create_dir(self):
        if not os.path.exists(self.builddir):
            os.makedirs(self.builddir)

    def configure_cmd(self, for_json=False):
        if for_json:
            return ('-C ' + self.preload_file
                    + ' ' + self.generator.configure_args(for_json))
        cmd = (['cmake', '-C', self.preload_file]
               + self.generator.configure_args())
        if self.kwargs.get('export_compile', False):
            cmd.append('-DCMAKE_EXPORT_COMPILE_COMMANDS=1')
        cmd += [  # '-DCMAKE_TOOLCHAIN_FILE='+toolchain_file,
            self.projdir]
        return cmd

    def configure(self):
        self.create_dir()
        self.create_preload_file()
        self.handle_deps()
        if self.needs_cache_regeneration():
            self.varcache.commit(self.builddir)
        with util.setcwd(self.builddir, silent=False):
            cmd = self.configure_cmd()
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
        with util.setcwd(self.builddir, silent=False):
            if self.needs_configure():
                self.configure()
            self.handle_deps()
            if len(targets) == 0:
                if self.compiler.is_msvc:
                    targets = ["ALL_BUILD"]
                else:
                    targets = ["all"]
            # cmake --build and visual studio won't handle
            # multiple targets at once, so loop over them.
            for t in targets:
                cmd = self.generator.cmd([t])
                util.runsyscmd(cmd)
            # this was written before using the loop above.
            # it can come to fail in some corner cases.
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
            if self.needs_cache_regeneration():
                return True
        return False

    def install(self):
        self.create_dir()
        with util.setcwd(self.builddir, silent=False):
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

    def _get_flagseq(self):
        return (self.flags, self.variant)

    def _gather_flags(self, which, append_to_sysinfo_var=None, with_defines=False):
        flags = []
        if append_to_sysinfo_var:
            try:
                flags = [CMakeSysInfo.var(append_to_sysinfo_var, self.generator)]
            except:
                pass

        # append overall build flags
        # append variant flags
        flagseq = self._get_flagseq()
        for fs in flagseq:
            wf = getattr(fs, which)
            for f in wf:
                r = f.get(self.compiler)
                flags.append(r)
            if with_defines:
                flags += fs.defines
        # we're done
        return flags

    def _gather_cmake_vars(self):
        flagseq = self._get_flagseq()
        for fs in flagseq:
            for v in fs.cmake_vars:
                spl = v.split('=')
                vval = ''.join(spl[1:]) if len(spl) > 1 else ''
                nspl = spl[0].split(':')
                if len(nspl) == 1:
                    self.varcache.setvar(nspl[0], vval, from_input=True)
                elif len(nspl) == 2:
                    self.varcache.setvar(nspl[0], vval, nspl[1], from_input=True)
                else:
                    raise Exception('could not parse variable value: ' + v)

    def gather_input_cache_vars(self):
        self._gather_cmake_vars()
        vc = self.varcache
        #
        def _set(pfn, pname, pval): pfn(pname, pval, from_input=True)
        if not self.generator.is_msvc:
            _set(vc.f, 'CMAKE_C_COMPILER', self.compiler.c_compiler)
            _set(vc.f, 'CMAKE_CXX_COMPILER', self.compiler.path)
        _set(vc.s, 'CMAKE_BUILD_TYPE', str(self.buildtype))
        _set(vc.p, 'CMAKE_INSTALL_PREFIX', self.installdir)
        #
        cflags = self._gather_flags('cflags', 'CMAKE_C_FLAGS_INIT', with_defines=True)
        if cflags:
            _set(vc.s, 'CMAKE_C_FLAGS', ' '.join(cflags))
        #
        cxxflags = self._gather_flags('cxxflags', 'CMAKE_CXX_FLAGS_INIT', with_defines=True)
        if cxxflags:
            _set(vc.s, 'CMAKE_CXX_FLAGS', ' '.join(cxxflags))
        #
        # if self.flags.include_dirs:
        #     _set(vc.s, 'CMANY_INCLUDE_DIRECTORIES', ';'.join(self.flags.include_dirs))
        #
        # if self.flags.link_dirs:
        #     _set(vc.s, 'CMAKE_LINK_DIRECTORIES', ';'.join(self.flags.link_dirs))
        #

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

    preload_file_tpl = ("""# Do not edit. Will be overwritten.
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
""" +
# """
# if(CMANY_INCLUDE_DIRECTORIES)
#     include_directories(${{CMANY_INCLUDE_DIRECTORIES}})
# endif()
#
# if(CMANY_LINK_DIRECTORIES)
#     link_directories(${{CMANY_LINK_DIRECTORIES}})
# endif()
# """ +
"""
# Do not edit. Will be overwritten.
# Generated by cmany on {date}
""")
    preload_file_tpl_empty = """# Do not edit. Will be overwritten.
# Generated by cmany on {date}

message(STATUS "cmany: nothing to preload...")
"""

    def handle_deps(self):
        if not self.deps:
            self.handle_conan()
            return
        util.lognotice(self.tag + ': building dependencies', self.deps)
        dup = copy.copy(self)
        dup.builddir = os.path.join(self.builddir, 'cmany_deps-build')
        dup.installdir = self.deps_prefix
        util.logwarn('installdir:', dup.installdir)
        dup.projdir = self.deps
        dup.preload_file = os.path.join(self.builddir, self.preload_file)
        dup.deps = None
        dup.generator.build = dup
        dup.configure()
        dup.build()
        try:
            # if the dependencies cmake project is purely consisted of
            # external projects, there won't be an install target.
            dup.install()
        except:
            pass
        util.logdone(self, ': building dependencies: done')
        util.logwarn('installdir:', dup.installdir)
        self.varcache.p('CMAKE_PREFIX_PATH', self.installdir)

    def handle_conan(self):
        if not self.kwargs.get('with_conan'):
            return
        doit = False
        f = None
        for fn in ('conanfile.py', 'conanfile.txt'):
            f = os.path.join(self.projdir, fn)
            cf = os.path.join(self.builddir, 'conanbuildinfo.cmake')
            if os.path.exists(f) and not os.path.exists(cf):
                doit = True
                break
        if not doit:
            return
        util.logdone('found conan file')
        c = Conan()
        c.install(self)

    def json_data(self):
        """
        https://blogs.msdn.microsoft.com/vcblog/2016/11/16/cmake-support-in-visual-studio-the-visual-studio-2017-rc-update/
        https://blogs.msdn.microsoft.com/vcblog/2016/12/20/cmake-support-in-visual-studio-2017-whats-new-in-the-rc-update/
        """
        builddir = self.builddir.replace(self.projdir, '${projectDir}')
        builddir = re.sub(r'\\', r'/', builddir)
        return odict([
            ('name', self.tag),
            ('generator', self.generator.name),
            ('configurationType', self.buildtype.name),
            ('buildRoot', builddir),
            ('cmakeCommandArgs', self.configure_cmd(for_json=True)),
            # ('variables', []),  # this is not needed since the vars are set in the preload file
        ])

    def get_targets(self):
        with util.setcwd(self.builddir):
            if self.generator.is_msvc:
                # each target in MSVC has a corresponding vcxproj file
                files = glob.glob(".", "*.vcxproj")
                files = [os.path.basename(f) for f in files]
                files = [os.path.splitext(f)[0] for f in files]
                return files
            elif self.generator.is_makefile:
                output = util.runsyscmd(["make", "help"], echo_cmd=False,
                                        echo_output=False, capture_output=True)
                output = output.split("\n")
                output = output[1:]  # The following are some of the valid targets....
                output = [o[4:] for o in output]  # take off the initial "... "
                output = [re.sub(r'(.*)\ \(the default if no target.*\)', r'\1', o) for o in output]
                output = sorted(output)
                result = []
                for o in output:
                    if o:
                        result.append(o)
                return result
            else:
                util.logerr("sorry, feature not implemented for this generator: " +
                            str(self.generator))

# -----------------------------------------------------------------------------
class ProjectConfig:

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

        self.configfile = os.path.join(proj_dir, "CMakeSettings.json")
        # self.configfile = None
        # if os.path.exists(configfile):
        #     self.parse_file(configfile)
        #     self.configfile = configfile
        flag_files = []
        for f in kwargs['flags_file']:
            if not os.path.isabs(f):
                f = os.path.join(self.root_dir, f)
            flag_files.append(f)
        c4flags.load_known_flags(flag_files, not kwargs['no_default_flags'])

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

    # def parse_file(self, configfile):
    #     raise Exception("not implemented")

    def add_build_if_valid(self, system, arch, buildtype, compiler, variant):
        if not self.is_valid(system, arch, buildtype, compiler, variant):
            return False
        # duplicate parameters for each build, as they may be mutated due
        # to translation of their flags for the compiler
        s = copy.deepcopy(system)
        a = copy.deepcopy(arch)
        t = copy.deepcopy(buildtype)
        c = copy.deepcopy(compiler)
        v = copy.deepcopy(variant)
        f = BuildFlags('all_builds', compiler, **self.kwargs)
        # create the build
        b = Build(self.root_dir, self.build_dir, self.install_dir,
                  s, a, t, c, v, f,
                  self.num_jobs, dict(self.kwargs))
        # When a build is created, its parameters may have been adjusted
        # because of an incompatible generator specification.
        # So drop this build if an equal one already exists
        if b.adjusted and self.exists(b):
            return False
        self.builds.append(b)
        return True

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
