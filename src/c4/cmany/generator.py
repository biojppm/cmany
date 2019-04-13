from . import cmake
from . import vsinfo

from .build_item import BuildItem
from .err import TooManyTargets


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
            more_args = name[1:]
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

    def cmd(self, targets, override_build_type=None, override_num_jobs=None):
        if self.is_makefile:
            return ['make', '-j', str(self.num_jobs)] + targets
        elif self.is_ninja:
            return ['ninja', '-j', str(self.num_jobs)] + targets
        else:
            bt = str(self.build.build_type)
            if len(targets) > 1:
                raise TooManyTargets(self)
            if not self.is_msvc:
                cmd = ['cmake', '--build', '.', '--target', targets[0], '--config', bt]
            else:
                # # if a target has a . in the name, it must be substituted for _
                # targets_safe = [re.sub(r'\.', r'_', t) for t in targets]
                # if len(targets_safe) != 1:
                #     raise Exception("msbuild can only build one target at a time: was " + str(targets_safe))
                # t = targets_safe[0]
                # pat = os.path.join(self.build.builddir, t + '*.vcxproj')
                # projs = glob.glob(pat)
                # if len(projs) == 0:
                #     msg = "could not find vcx project for this target: {} (glob={}, got={})".format(t, pat, projs)
                #     raise Exception(msg)
                # elif len(projs) > 1:
                #     msg = "multiple vcx projects for this target: {} (glob={}, got={})".format(t, pat, projs)
                #     raise Exception(msg)
                # proj = projs[0]
                # cmd = [self.build.compiler.vs.msbuild, proj,
                #        '/property:Configuration='+bt,
                #        '/maxcpucount:' + str(self.num_jobs)]
                cmd = ['cmake', '--build', '.', '--target', targets[0], '--config', bt,
                       '--',
                       #'/property:Configuration='+bt,
                       '/maxcpucount:' + str(self.num_jobs)]
            return cmd

    def install(self):
        bt = str(self.build.build_type)
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
    Visual Studio 16 2019 -A [Win32|x64|ARM|ARM64]

    Green Hills MULTI
    Xcode
    """
