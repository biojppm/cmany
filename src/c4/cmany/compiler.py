import os
import re
import tempfile

from .build_item import BuildItem
from .system import System
from .cmake import CMakeSysInfo
from . import util
from . import vsinfo


# -----------------------------------------------------------------------------
class Compiler(BuildItem):
    """Represents a compiler choice"""

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

    def __init__(self, spec):
        if util.is_quoted(spec):
            spec = util.unquote(spec)
        spl = spec.split(':')
        path = spl[0]
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
        self.name_for_flags = self.shortname
        if self.is_msvc:
            if self.vs.is_clang:
                self.name_for_flags = 'clang'
            else:
                self.name_for_flags = 'vs'
        # don't forget: a build item should be initialized with the full spec
        if len(spl) > 1:
            # change the spec to reflect the real compiler name
            spec = name + ": " + ":".join(spl[1:])
        else:
            spec = name
        super().__init__(spec)
        # maybe we should use a different way to get the c compiler.
        # For now this will do.
        self.c_compiler = __class__.get_c_compiler(self.shortname, self.path)

    @staticmethod
    def get_c_compiler(shortname, cxx_compiler):
        # if cxx_compiler.endswith("c++") or cxx_compiler.endswith('c++.exe'):
        #     cc = re.sub(r'c\+\+', r'cc', cxx_compiler)
        if shortname.startswith('vs') or re.search(r'sual Studio', cxx_compiler):
            cc = cxx_compiler
        elif shortname == "icc" or shortname == "icpc":
            cc = re.sub(r'icpc', r'icc', cxx_compiler)
        elif shortname == "gcc" or shortname == "g++":
            cc = re.sub(r'g\+\+', r'gcc', cxx_compiler)
        elif shortname == "clang" or shortname == "clang++":
            cc = re.sub(r'clang\+\+', r'clang', cxx_compiler)
        elif shortname == "c++":
            cc = "cc"
        elif shortname.startswith("arm-"):
            cc = re.sub(r'g\+\+', 'gcc', shortname)
        else:
            cc = "cc"
        return cc

    def get_version(self, path):
        # a function to silently run a system command
        def slntout(cmd):
            out = util.runsyscmd(cmd, echo_cmd=False,
                                 echo_output=False, capture_output=True)
            out = out.strip("\n")
            return out
        # is this visual studio?
        if hasattr(self, "vs"):
            return self.vs.name, str(self.vs.year), self.vs.name
        # other compilers
        # print("cmp: found compiler:", path)
        out = slntout([path, '--version'])
        version_full = out.split("\n")[0]
        splits = version_full.split(" ")
        name = splits[0].lower()
        # print("cmp: version:", name, "---", version_full, "---")
        vregex = r'(\d+\.\d+)\.\d+'
        base = os.path.basename(path)
        # print("cmp base:", base)
        if base.startswith("c++") or base.startswith("cc"):
            with tempfile.NamedTemporaryFile(suffix=".cc", prefix="cmany.", delete=False) as f:
                macros = slntout([path, '-dM', '-E', f.name])
                os.unlink(f.name)
            macros = macros.split("\n")
            for m in sorted(macros):
                if re.search("#define __GNUC__", m):
                    name = "g++" if base.startswith("c++") else "gcc"
                elif re.search("#define __clang__", m):
                    name = "clang++" if base.startswith("c++") else "clang"
                    break
        if name.startswith("g++") or name.startswith("gcc"):
            # print("g++: version:", name, name.find('++'))
            name = "g++" if name.find('++') != -1 else 'gcc'
            # print("g++: version:", name, name.find('++'))
            version = slntout([path, '-dumpversion'])
            version = re.sub(vregex, r'\1', version)
            # print("gcc version:", version, "---")
        elif name.startswith("clang"):
            name = "clang++" if path.find('clang++') != -1 else 'clang'
            version = re.sub(r'clang version ' + vregex + '.*', r'\1', version_full)
            # print("clang version:", version, "---")
        elif name.startswith("icpc") or name.startswith("icc"):
            name = "icc" if name.startswith("icc") else "icpc"
            if re.search(r'icpc \(ICC\) ' + vregex + '.*'):
                version = re.sub(r'icpc \(ICC\) ' + vregex + '.*', r'\1', version_full)
            else:
                version = re.sub(r'icc \(ICC\) ' + vregex + '.*', r'\1', version_full)
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
