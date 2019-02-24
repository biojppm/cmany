import os
import copy
import re
import dill
from datetime import datetime

from .generator import Generator
from . import util, cmake, vsinfo
from .named_item import NamedItem
from .variant import Variant
from .build_flags import BuildFlags
from .compiler import Compiler
from .architecture import Architecture

# experimental. I don't think it will stay unless conan starts accepting args
from .conan import Conan


# -----------------------------------------------------------------------------
class Build(NamedItem):
    """Holds a build's settings"""

    pfile = "cmany_preload.cmake"
    sfile = "cmany_build.dill"

    def __init__(self, proj_root, build_root, install_root,
                 system, arch, build_type, compiler, variant, flags,
                 num_jobs, kwargs):
        #
        self.kwargs = kwargs
        self.export_compile = self.kwargs.get('export_compile', True)
        #
        self.projdir = util.chkf(proj_root)
        self.buildroot = os.path.abspath(build_root)
        self.installroot = os.path.abspath(install_root)
        #
        self.flags = flags
        self.system = system
        self.architecture = arch
        self.build_type = build_type
        self.compiler = compiler
        self.variant = variant
        #
        self.adjusted = False
        #
        if util.in_64bit and self.architecture.is32:
            if self.compiler.gcclike:
                self.compiler.make_32bit()
        elif util.in_32bit and self.architecture.is64:
            if self.compiler.gcclike:
                self.compiler.make_64bit()
        #
        tag = self._set_name_and_paths()
        super().__init__(tag)
        #
        self.toolchain_file = self._get_toolchain()
        if self.toolchain_file:
            comps = cmake.extract_toolchain_compilers(self.toolchain_file)
            c = Compiler(comps['CMAKE_CXX_COMPILER'])
            self.adjust(compiler=c)
        #
        # WATCHOUT: this may trigger a readjustment of this build's parameters
        self.generator = self.create_generator(num_jobs)
        #
        # This will load the vars from the builddir cache, if it exists.
        # It should be done only after creating the generator.
        self.varcache = cmake.CMakeCache(self.builddir)
        # ... and this will overwrite (in memory) the vars with the input
        # arguments. This will make the cache dirty and so we know when it
        # needs to be committed back to CMakeCache.txt
        self.gather_input_cache_vars()
        #
        self.deps = kwargs.get('deps', '')
        if self.deps and not os.path.isabs(self.deps):
            self.deps = os.path.abspath(self.deps)
        self.deps_prefix = kwargs.get('deps_prefix')
        if self.deps_prefix and not os.path.isabs(self.deps_prefix):
            self.deps_prefix = os.path.abspath(self.deps_prefix)
        if not self.deps_prefix:
            self.deps_prefix = self.builddir

    def _set_name_and_paths(self):
        self.tag = __class__.get_tag(
            self.system, self.architecture,
            self.compiler, self.build_type, self.variant, '-')
        self.buildtag = self.tag
        self.installtag = self.tag  # this was different in the past and may become so in the future
        self.builddir = os.path.abspath(os.path.join(self.buildroot, self.buildtag))
        self.installdir = os.path.join(self.installroot, self.installtag)
        self.preload_file = os.path.join(self.builddir, Build.pfile)
        self.cachefile = os.path.join(self.builddir, 'CMakeCache.txt')
        return self.tag

    def create_generator(self, num_jobs, fallback_generator="Unix Makefiles"):
        """create a generator, adjusting the build parameters if necessary"""
        #if self.toolchain_file is not None:
        #    toolchain_cache = cmake.get_toolchain_cache(self.toolchain_file)
        #    print(toolchain_cache)
        #    self.adjust(compiler=toolchain_cache['CMAKE_CXX_COMPILER'])
        if self.compiler.is_msvc:
            vsi = vsinfo.VisualStudioInfo(self.compiler.name)
            g = Generator(vsi.gen, self, num_jobs)
            arch = Architecture(vsi.architecture)
            self.adjust(architecture=arch)
            self.vsinfo = vsi
            return g
        else:
            if self.system.name == "windows":
                return Generator(fallback_generator, self, num_jobs)
            else:
                return Generator(Generator.default_str(), self, num_jobs)

    def adjust(self, **kwargs):
        for k, _ in kwargs.items():
            if k not in ('architecture', 'compiler'):
                raise Exception("build adjustment for {} not supported".format(k))
        a = kwargs.get('architecture')
        if a and a != self.architecture:
            self.adjusted = True
            self.architecture = a
        c = kwargs.get('compiler')
        if c and c != self.compiler:
            self.adjusted = True
            self.compiler = c
        self._set_name_and_paths()

    @staticmethod
    def get_tag(s, a, c, t, v, sep='-'):
        # some utilities (eg, ar) dont deal well with + in the path
        # so replace + with x
        # eg see https://sourceforge.net/p/mingw/bugs/1429/
        sc = __class__.sanitize_compiler_name(c)
        s = str(s) + sep + str(a) + sep + sc + sep + str(t)
        if v is not None and isinstance(v, Variant):
            v = v.name
        if v and v != "none":
            s += "{sep}{var}".format(sep=sep, var=str(v))
        return s

    @staticmethod
    def sanitize_compiler_name(c):
        sc = re.sub(r'\+', 'x', str(c))
        return sc

    def create_dir(self):
        if not os.path.exists(self.builddir):
            os.makedirs(self.builddir)

    def _serialize(self):
        # https://stackoverflow.com/questions/4529815/saving-an-object-data-persistence
        protocol = 0  # serialize in ASCII
        fn = os.path.join(self.builddir, __class__.sfile)
        with open(fn, 'wb') as f:
            dill.dump(self, f, protocol)

    @staticmethod
    def deserialize(builddir):
        # https://stackoverflow.com/questions/4529815/saving-an-object-data-persistence
        if not os.path.exists(builddir):
            msg = "build directory does not exist: {}"
            raise Exception(msg.format(builddir))
        fn = os.path.join(builddir, __class__.sfile)
        with open(fn, 'rb') as f:
            return dill.load(f)

    def configure_cmd(self, for_json=False):
        if for_json:
            return ('-C ' + self.preload_file
                    + ' ' + self.generator.configure_args(for_json=for_json))
        cmd = (['cmake', '-C', self.preload_file]
               + self.generator.configure_args(export_compile_commands=self.export_compile))
        if self.toolchain_file:
            cmd.append('-DCMAKE_TOOLCHAIN_FILE=' + self.toolchain_file)
        cmd.append(self.projdir)
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
        if self.export_compile:
            if not self.generator.exports_compile_commands:
                util.logwarn("WARNING: this generator cannot export compile commands. Use 'cmany export_compile_commands/xcc to export the compile commands.'")

    def export_compile_commands(self):
        # some generators (notably VS/msbuild) cannot export compile
        # commands, so to get that, we'll configure a second build using the
        # ninja generator so that compile_commands.json is generated;
        # finally, copy over that file to this build directory
        if self.needs_configure():
            self.configure()
        trickdir = os.path.join(self.builddir, '.export_compile_commands')
        if not os.path.exists(trickdir):
            os.makedirs(trickdir)
        with util.setcwd(trickdir, silent=False):
            cmd = ['cmake', '-G', 'Ninja', '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON', '-C', self.preload_file, self.projdir]
            if not self.compiler.is_msvc:
                util.runsyscmd(cmd)
            else:
                self.vsinfo.runsyscmd(cmd)
        src = os.path.join(trickdir, "compile_commands.json")
        dst = os.path.join(self.builddir, "compile_commands.json")
        if os.path.exists(src):
            from shutil import copyfile
            if os.path.exists(dst):
                os.remove(dst)
            copyfile(src, dst)
            util.loginfo("exported compile_commands.json:", dst)

    def reconfigure(self):
        """reconfigure a build directory, without touching any cache entry"""
        self._check_successful_configure('reconfigure')
        with util.setcwd(self.builddir, silent=False):
            cmd = ['cmake', self.projdir]
            util.runsyscmd(cmd)

    def _check_successful_configure(self, purpose):
        if not os.path.exists(self.builddir):
            msg = "cannot {}: build dir does not exist: {}"
            raise Exception(msg.format(purpose, self.builddir))
        if not os.path.exists(self.varcache.cache_file):
            msg = "cannot {}: cache file not found: {}"
            raise Exception(msg.format(purpose, self.varcache.cache_file))
        pkf = os.path.join(self.builddir, __class__.sfile)
        if not os.path.exists(pkf):
            msg = "cannot {}: build save file not found: {}"
            raise Exception(msg.format(purpose, pkf))

    def mark_configure_done(self, cmd):
        self._serialize()
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

    def rebuild(self, targets=[]):
        self._check_successful_configure('rebuild')
        with util.setcwd(self.builddir, silent=False):
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
            util.runsyscmd(cmd)

    def reinstall(self):
        self._check_successful_configure('reinstall')
        with util.setcwd(self.builddir, silent=False):
            if self.needs_build():
                self.build()
            cmd = self.generator.install()
            util.runsyscmd(cmd)

    def clean(self):
        self.create_dir()
        with util.setcwd(self.builddir):
            cmd = self.generator.cmd(['clean'])
            util.runsyscmd(cmd)
            os.remove("cmany_build.done")

    def _get_flagseq(self):
        return (
            self.flags,
            self.system.flags,
            self.architecture.flags,
            self.compiler.flags,
            self.build_type.flags,
            self.variant.flags
        )

    def _get_toolchain(self):
        tc = None
        for fs in self._get_flagseq():
            tc = BuildFlags.merge_toolchains(tc, fs.toolchain)
        if not tc:
            return None
        if not os.path.isabs(tc):
            tc = os.path.join(os.getcwd(), tc)
            tc = os.path.abspath(tc)
        if not os.path.exists(tc):
            raise Exception("file not found: " + tc)
        return tc

    def _gather_flags(self, which, append_to_sysinfo_var=None, with_defines=False):
        flags = []
        if append_to_sysinfo_var:
            try:
                flags = [cmake.CMakeSysInfo.var(append_to_sysinfo_var, self.generator)]
            except Exception as e:
                pass
        # append overall build flags
        # append variant flags
        flagseq = self._get_flagseq()
        for fs in flagseq:
            wf = getattr(fs, which)
            for f in wf:
                if isinstance(f, str):
                    r = f
                elif isinstance(f, CFlag):
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
        if (not self.generator.is_msvc) and (not self.toolchain_file):
            _set(vc.f, 'CMAKE_C_COMPILER', self.compiler.c_compiler)
            _set(vc.f, 'CMAKE_CXX_COMPILER', self.compiler.path)
        _set(vc.s, 'CMAKE_BUILD_TYPE', str(self.build_type))
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
            tpl = _preload_file_tpl
        else:
            tpl = _preload_file_tpl_empty
        now = datetime.now().strftime("%Y/%m/%d %H:%m")
        txt = tpl.format(date=now, vars="\n".join(lines))
        with open(self.preload_file, "w") as f:
            f.write(txt)
        return self.preload_file

    @property
    def deps_done(self):
        dmark = os.path.join(self.builddir, "cmany_deps.done")
        exists = os.path.exists(dmark)
        return exists

    def mark_deps_done(self):
        with util.setcwd(self.builddir):
            with open("cmany_deps.done", "w") as f:
                s = ''
                if self.deps:
                    s += self.deps + '\n'
                if self.deps_prefix:
                    s += self.deps_prefix + '\n'
                f.write(s)

    def handle_deps(self):
        if self.deps_done:
            return
        if not self.deps:
            self.handle_conan()
            self.mark_deps_done()
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
        except Exception as e:
            util.logwarn(self.name + ": could not install. Maybe there's no install target?")
        util.logdone(self.name + ': finished building dependencies. Install dir=', self.installdir)
        self.varcache.p('CMAKE_PREFIX_PATH', self.installdir)
        self.mark_deps_done()

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
            ('configurationType', self.build_type.name),
            ('buildRoot', builddir),
            ('cmakeCommandArgs', self.configure_cmd(for_json=True)),
            # ('variables', []),  # this is not needed since the vars are set in the preload file
        ])

    def get_targets(self):
        with util.setcwd(self.builddir):
            if self.generator.is_msvc:
                # each target in MSVC has a corresponding vcxproj file
                files = list(util.find_files_with_ext(self.builddir, ".vcxproj"))
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

    def show_properties(self):
        util.logcmd(self.name)
        p = lambda n, v: print("{}={}".format(n, v))
        if self.toolchain_file:
            p('CMAKE_TOOLCHAIN_FILE', self.toolchain_file)
        p('CMAKE_C_COMPILER', self.compiler.c_compiler)
        p('CMAKE_CXX_COMPILER', self.compiler.path)
        dont_show = ('CMAKE_INSTALL_PREFIX', 'CMAKE_CXX_COMPILER', 'CMAKE_C_COMPILER')
        for _, v in self.varcache.items():
            if v.from_input:
                if v.name in dont_show:
                    continue
                p(v.name, v.val)
        p("PROJECT_BINARY_DIR", self.builddir)
        p("CMAKE_INSTALL_PREFIX", self.installdir)


# -----------------------------------------------------------------------------
_preload_file_tpl = ("""\
# Do not edit. Will be overwritten.
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

# if(CMANY_INCLUDE_DIRECTORIES)
#     include_directories(${{CMANY_INCLUDE_DIRECTORIES}})
# endif()
#
# if(CMANY_LINK_DIRECTORIES)
#     link_directories(${{CMANY_LINK_DIRECTORIES}})
# endif()

# Do not edit. Will be overwritten.
# Generated by cmany on {date}
""")

# -----------------------------------------------------------------------------
_preload_file_tpl_empty = ("""\
# Do not edit. Will be overwritten.
# Generated by cmany on {date}

message(STATUS "cmany: nothing to preload...")
""")
