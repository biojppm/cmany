from . import cmake
from . import vsinfo
from . import err

from .build_item import BuildItem
from .err import TooManyTargets

"""
generators: https://cmake.org/cmake/help/latest/manual/cmake-generators.7.html

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
Visual Studio 16 2019 -A [Win32|x64|ARM|ARM64]

Green Hills MULTI
Xcode
"""

# -----------------------------------------------------------------------------
class Generator(BuildItem):

    """Visual Studio aliases example:
    vs2013: use the bitness of the current system
    vs2013_32: use 32bit version
    vs2013_64: use 64bit version
    """

    @staticmethod
    def default_str():
        """get the default generator from cmake"""
        s = cmake.CMakeSysInfo.generator()
        return s

    def __init__(self, name, build, num_jobs):
        if isinstance(name, list):
            #more_args = name[1:]
            name = name[0]
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
        # EXPORT_COMPILE_COMMANDS is valid only for makefiles and ninja generators
        # https://cmake.org/cmake/help/v3.14/variable/CMAKE_EXPORT_COMPILE_COMMANDS.html
        self.exports_compile_commands = (self.is_makefile or self.is_ninja)
        # these vars would not change cmake --system-information
        # self.full_name += " ".join(self.build.flags.cmake_vars)

    def configure_args(self, for_json=False, export_compile_commands=True):
        args = []
        if self.name != "":
            if self.is_msvc:
                vs = self.build.compiler.vs
                if not for_json:
                    if isinstance(vs.gen, str):
                        args += ['-G', vs.gen]
                    elif isinstance(vs.gen, list):
                        args += ['-G'] + vs.gen
                if vs.toolset is not None:
                    args += ['-T', vs.toolset]
            else:
                if not for_json:
                    args += ['-G', self.name]
        # cmake vars are explicitly set in the preload file
        # args += self.build.flags.cmake_flags
        if self.is_makefile or self.is_ninja:
            args.append("-DCMAKE_EXPORT_COMPILE_COMMANDS=ON")
        elif self.is_msvc:
            pass
        return args

    @property
    def target_all(self):
        "return the name of the ALL target"
        return "ALL_BUILD" if self.is_msvc else "all"

    def cmd(self, targets):
        if self.is_makefile:
            return ['make', '-j', str(self.num_jobs)] + targets
        elif self.is_ninja:
            return ['ninja', '-j', str(self.num_jobs)] + targets
        else:
            bt = str(self.build.build_type)
            if len(targets) > 1:
                raise TooManyTargets(self)
            cmd = ['cmake', '--build', '.', '--config', bt, '--target', targets[0],
                   '--parallel', str(self.num_jobs)]
            return cmd

    def cmd_source_file(self, target, source_file):
        """get a command to build a source file
        https://stackoverflow.com/questions/38271387/compile-a-single-file-under-cmake-project
        """
        relpath = os.path.relpath(source_file, os.path.abspath(self.build.builddir))
        if self.is_makefile:
            return ['make', relpath]
        elif self.is_ninja:
            raise err.NotImplemented()
            # https://ninja-build.org/manual.html#_running_ninja
            return ['ninja', f'{relpath}^']
        else:
            bt = str(self.build.build_type)
            cmd = ['cmake', '--build', '.', '--target', targets[0], '--config', bt]
            return cmd

    def install(self):
        bt = str(self.build.build_type)
        return ['cmake', '--build', '.', '--config', bt, '--target', 'install']

    def clean_msbuild_target_name(self, target_name):
        # if a target has a . in the name, it must be substituted for _
        target_safe = re.sub(r'\.', r'_', target_name)


