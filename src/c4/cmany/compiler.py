import os
import re
import tempfile
import shlex

from .build_item import BuildItem
from .system import System
from .cmake import CMakeSysInfo
from . import util
from . import vsinfo
from . import err
from .util import logdbg


def dbg(*args, **kwargs):
    logdbg("compiler:", *args, **kwargs)


# -----------------------------------------------------------------------------
class Compiler(BuildItem):
    """Represents a compiler choice"""

    @staticmethod
    def default(toolchain_file: str=None):
        return Compiler(__class__.default_str(toolchain_file))

    @staticmethod
    def default_str(toolchain_file: str=None):
        if str(System.default(toolchain_file)) != "windows":
            cpp = CMakeSysInfo.cxx_compiler(toolchain=toolchain_file)
        else:
            vs = vsinfo.find_any()
            cpp = vs.name if vs is not None else CMakeSysInfo.cxx_compiler(toolchain_file)
        return cpp

    def is_trivial(self):
        """reimplement BuildItem.is_trivial because our name is altered from the
        path to compiler_name+version"""
        if self.path != self.default_str():
            return False
        if not self.flags.empty():
            return False
        return True

    def __init__(self, spec):
        if util.is_quoted(spec):
            spec = util.unquote(spec)
        spl = spec.split(':')
        path = spl[0]
        if path.startswith("vs") or path.startswith("Visual Studio"):
            if not util.in_windows():
                raise err.CompilerNotFound(spec, "visual studio is only available in windows platforms")
            vs = vsinfo.VisualStudioInfo(path)
            self.vs = vs
            path = vs.cxx_compiler
        else:
            # in windows, defend against paths written for example as
            # C:\path\to\compiler. The split is inappropriate here.
            if (util.in_windows() and len(path) == 1 and len(spl) > 1 and (spl[1][0] == '/' or spl[1][0] == '\\')):
                path = spec
                spl = [path]
            p = util.which(path)
            if p is None:
                dbg("not found:", path)
                shspl = shlex.split(path)
                dbg("trying split:", shspl)
                if len(shspl) > 0:
                    p = util.which(shspl[0])
                    dbg("trying split:", p)
            if p is None:
                dbg("no compiler found", path)
                raise err.CompilerNotFound(path)
            if p != path:
                dbg("selected {} for {}".format(p, path))
            if isinstance(path, str):
                path = os.path.abspath(p)
            else:
                path[0] = os.path.abspath(p)
        name, version, version_full = self.get_version(path)
        self.shortname = name
        self.gcclike = self.shortname in ('gcc', 'clang', 'icc', 'g++', 'clang++', 'icpc', 'icpx')
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
        elif shortname == "icpx":
            cc = re.sub(r'icpx', r'icpx', cxx_compiler)
        elif shortname == "gcc" or shortname == "g++" or shortname.startswith("g++"):
            if re.search(r'g\+\+', cxx_compiler):
                cc = re.sub(r'g\+\+', r'gcc', cxx_compiler)
            else:
                cc = re.sub(r'c\+\+', r'cc', cxx_compiler)
        elif shortname == "clang" or shortname == "clang++" or shortname.startswith("clang++"):
            if re.search(r'clang\+\+', cxx_compiler):
                cc = re.sub(r'clang\+\+', r'clang', cxx_compiler)
            else:
                cc = re.sub(r'c\+\+', r'cc', cxx_compiler)
        elif shortname.startswith("arm-"):
            cc = re.sub(r'g\+\+', 'gcc', cxx_compiler)
        elif re.search(r"c\+\+", shortname) or re.search(r'apple_llvm', shortname):
            cc = re.sub(r"c\+\+", "cc", cxx_compiler)
        else:
            cc = "cc"
        return cc

    def get_version(self, path):
        # a function to silently run a system command
        slntout = util.get_output
        # is this visual studio?
        if hasattr(self, "vs"):
            return self.vs.name, str(self.vs.year), self.vs.name
        # other compilers
        dbg("found compiler:", path)
        if isinstance(path, str):
            out = slntout([path, '--version'])
        else:
            out = slntout(path + ['--version'])
        version_full = out.split("\n")[0]
        splits = version_full.split(" ")
        name = splits[0].lower()
        dbg("version:", name, "---", version_full, "---")
        vregex = r'(\d+\.\d+)\.\d+'
        base = os.path.basename(path)
        dbg("base:", base)
        dbg("name:", name)
        if base.startswith("c++") or base.startswith("cc"):
            try:  # if this fails, just go on. It's not really needed.
                with tempfile.NamedTemporaryFile(suffix=".cpp", prefix="cmany.", delete=False) as f:
                    macros = slntout([path, '-dM', '-E', f.name])
                    os.unlink(f.name)
                macros = macros.split("\n")
            except Exception as e:
                macros = []
            for m in sorted(macros):
                if re.search("#define __clang__", m):
                    name = "clang++" if re.search(r"\+\+", path) else "clang"
                    break
                elif re.search("#define __GNUC__", m):
                    name = "g++" if re.search(r"\+\+", path) else "gcc"
                    break
        elif version_full.startswith("Ubuntu clang version"):
            name = "clang++"
        # not elif!
        if name.startswith("clang++") or name.startswith("clang") or name.endswith("clang++") or name.endswith("clang"):
            name = "clang++" if path.find('clang++') != -1 else 'clang'
            if re.search('Apple LLVM', version_full):
                name = "apple_llvm"
                version = re.sub(r'Apple LLVM version ' + vregex + '.*', r'\1', version_full)
                dbg("apple_llvm version:", version, "---")
            elif version_full.startswith("Ubuntu clang version"):
                name = "clang++"
                version = re.sub('Ubuntu clang version ' + vregex + '.*', r'\1', version_full)
            else:
                version = re.sub(r'clang version ' + vregex + '.*', r'\1', version_full)
            dbg("clang version:", version, "---")
        elif name.startswith("g++") or name.startswith("gcc") or name.endswith("g++") or name.endswith("gcc"):
            dbg("g++: name=", name)
            if (name.startswith("g++") and name != "g++"):
                name = "g++"
            if (name.startswith("gcc") and name != "gcc"):
                name = "gcc"
            dbg("g++: name=", name)
            #name = "g++" if name.find('++') != -1 else 'gcc'
            #dbg("g++: version:", name, name.find('++'))
            version = slntout([path, '-dumpversion'])
            dbg("g++: versiondump:", version)
            dbg("g++: versionfull:", version_full)
            version = re.sub(vregex, r'\1', version)
            dbg("gcc version:", version, "---")
        elif name.startswith("icpc") or name.startswith("icc"):
            name = "icc" if name.startswith("icc") else "icpc"
            if re.search(r'icpc \(ICC\) ' + vregex + '.*', version_full):
                version = re.sub(r'icpc \(ICC\) ' + vregex + '.*', r'\1', version_full)
            else:
                version = re.sub(r'icc \(ICC\) ' + vregex + '.*', r'\1', version_full)
            dbg("icc version:", version, "---")
        elif version_full.startswith("Intel(R) oneAPI"):
            name = "intel"
            rx = r'Intel\(R\) oneAPI .*? Compiler ([0-9.]*?) \(([0-9.]*?)\).*'
            version = re.sub(rx, r'\1', version_full)
            version_full = re.sub(rx, r'\2', version_full)
            dbg("intel version:", version, "---", version_full)
        else:
            version = slntout([path, '-dumpversion'])
            version = re.sub(vregex, r'\1', version)
        #
        return name, version, version_full

    def make_32bit(self):
        if self.gcclike:
            self.flags.cflags.append('-m32')
            self.flags.cxxflags.append('-m32')

    def make_64bit(self):
        if self.gcclike:
            self.flags.cflags.append('-m64')
            self.flags.cxxflags.append('-m64')
