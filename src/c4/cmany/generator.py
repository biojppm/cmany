from . import cmake
from . import vsinfo
from . import err
from . import util

from .build_item import BuildItem
from .err import TooManyTargets
from .util import logdbg

import fnmatch
import os
import shlex


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
class Generator(BuildItem):  # NamedItem

    """Visual Studio aliases example:
    vs2013: use the bitness of the current system
    vs2013_32: use 32bit version
    vs2013_64: use 64bit version
    """

    @staticmethod
    def default_str(toolchain_file: str=None):
        """get the default generator from cmake"""
        s = cmake.CMakeSysInfo.generator(toolchain_file)
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

    @property
    def verbose(self):
        return self.build.verbose

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
            if self.verbose:
                return ['make', 'VERBOSE=1', '-j', str(self.num_jobs)] + targets
            else:
                return ['make', '-j', str(self.num_jobs)] + targets
        elif self.is_ninja:
            if self.verbose:
                return ['ninja', '--verbose', '-j', str(self.num_jobs)] + targets
            else:
                return ['ninja', '-j', str(self.num_jobs)] + targets
        else:
            if len(targets) > 1:
                raise TooManyTargets(self)
            target = targets[0]
            bt = str(self.build.build_type)
            # NOTE:
            # the `--parallel` flag to `cmake --build` is broken in VS and XCode:
            # https://discourse.cmake.org/t/parallel-does-not-really-enable-parallel-compiles-with-msbuild/964/10
            # https://gitlab.kitware.com/cmake/cmake/-/issues/20564
            if not self.is_msvc:
                cmd = ['cmake', '--build', '.', '--target', target, '--config', bt,
                       '--parallel', str(self.num_jobs)]
                if self.verbose:
                    cmd.append('--verbose')
                # TODO XCode is also broken; the flag is this:
                # -IDEBuildOperationMaxNumberOfConcurrentCompileTasks=$NUM_JOBS_BUILD
                # see:
                # https://stackoverflow.com/questions/5417835/how-to-modify-the-number-of-parallel-compilation-with-xcode
                # https://gist.github.com/nlutsenko/ee245fbd239087d22137
            else:
                cmd = ['cmake', '--build', '.', '--target', target, '--config', bt]
                if self.verbose:
                    cmd.append('--verbose')
                cmd += ['--', '/maxcpucount:' + str(self.num_jobs)]
                # old code for building through msbuild:
                # # if a target has a . in the name, it must be substituted for _
                # targets_safe = [re.sub(r'\.', r'_', t) for t in targets]
                # if len(targets_safe) != 1:
                #     raise TooManyTargets("msbuild can only build one target at a time: was " + str(targets_safe))
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
            return cmd

    def cmd_source_file(self, source_file, target):
        """get a command to build a source file"""
        logdbg("building source file:", source_file, "from target", target)
        relpath = os.path.relpath(source_file, os.path.abspath(self.build.builddir))
        logdbg("building source file: relpath:", relpath)
        basecmd = ['cmake', '--build', '.', '--target', target, '--verbose']  # always verbose
        if self.is_makefile:
            # https://stackoverflow.com/questions/38271387/compile-a-single-file-under-cmake-project
            return basecmd + ['--', relpath]
        elif self.is_ninja:
            # https://ninja-build.org/manual.html#_running_ninja
            #return ['ninja', f'{relpath}^']
            return basecmd + ['--', f'{relpath}^']
        elif not self.is_msvc:
            raise err.NotImplemented("don't know how to build source files in this generator")
        else:
            # msvc:
            # https://stackoverflow.com/questions/4172438/using-msbuild-to-compile-a-single-cpp-file
            #return basecmd + ['--config', str(self.build.build_type), '--',
            #                  '-t:ClCompile', f'-p:SelectedFiles={relpath}']
            #
            # the command does not result in compiling ONLY the requested file.
            # It fails because -p:SelectedFiles is ignored, so the command
            # builds the whole target.
            #
            # So we have to get really down and dirty...
            logdbg("generator is vs -- need to discover the cl command line")
            cl_cmd = self.vs_cl_cmd(source_file, target)
            logdbg("cl_cmd=", cl_cmd)
            return cl_cmd

    def install(self):
        bt = str(self.build.build_type)
        return ['cmake', '--build', '.', '--config', bt, '--target', 'install']

    def vs_cl_cmd(self, source_file, target):
        tlog = self.vs_find_cl_cmd_tlog(target)
        abspath = os.path.join(self.build.projdir, source_file)
        cl_cmd = tlog.get_cmd_line(abspath)
        cxx_compiler = self.build.cxx_compiler
        cl_cmd = " ".join(shlex.split(f'"{cxx_compiler}" {cl_cmd}', posix=False))
        dev_cmd = " ".join(self.build.vs_dev_cmd(target))
        return f"{dev_cmd} {cl_cmd}"

    def vs_find_cl_cmd_tlog(self, target):
        vcxproj = self.vs_get_vcxproj(target)
        variant = vcxproj.get_variant(str(self.build.build_type), self.build.architecture)
        tlog_dir = util.chkf(f"{variant.intdir}/{target}.tlog")
        tlog = util.chkf(f"{tlog_dir}/CL.command.1.tlog")
        return vsinfo.ClCommandTlog(tlog)

    def vs_get_vcxproj(self, target):
        class Foo: pass
        store = util.cacheattr(self, 'vs_target_vcxproj', lambda: Foo())
        vcxproj = util.cacheattr(store, target, lambda: vsinfo.VcxProj(self.vs_find_vcxproj(target)))
        return vcxproj

    def vs_find_vcxproj(self, target):
        logdbg("searching for vcxproj:", target)
        matches = []
        for root, dirnames, filenames in os.walk(self.build.builddir):
            for filename in fnmatch.filter(filenames, f"{target}.vcxproj"):
                matches.append(os.path.join(root, filename))
        if len(matches) == 0:
            raise err.NotImplemented(f"could not find vcxproj: {target}")
        if len(matches) > 1:
            raise err.NotImplemented("cannot deal with multiple targets with the same name")
        vcxproj = os.path.realpath(matches[0])
        logdbg("found vcxproj:", vcxproj)
        return vcxproj
