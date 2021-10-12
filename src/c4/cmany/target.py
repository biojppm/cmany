import os
from enum import IntFlag

from . import util
from . import vsinfo


class TargetType(IntFlag):
    custom = 0  # a custom target
    binary = 1  # a library or executable
    interm = 2  # intermediate target from source code file (eg .o, .s, .i)
    def __str__(self):
        return self.name


class Target:

    def _dbg(self, msg):
        util.logdbg(f"[{self.subdir}] {self.name}: {msg}")

    def __init__(self, name, build, subdir, projfile):
        assert os.path.exists(projfile)
        self.name = name
        self.build = build
        self.subdir = subdir
        self.subdir_abs = os.path.join(os.path.abspath(build.builddir), self.subdir)
        self.projfile = projfile  # Makefile or {name}.vcxproj
        self.cmake_private_dir = util.chkf(self.subdir_abs, "CMakeFiles")
        self._dbg("creating target...")
        # find the target type
        self._type = TargetType.custom
        gen = self.build.generator
        if gen.is_msvc:
            tgt_dir = os.path.join(self.subdir_abs, f"{name}.dir")
            if os.path.exists(tgt_dir):
                self._dbg(f"target is binary: found {tgt_dir}")
                self._type |= TargetType.binary
        elif gen.is_makefile:
            tgt_dir = os.path.join(self.cmake_private_dir, f"{name}.dir")
            link_file = os.path.join(tgt_dir, "link.txt")
            if os.path.exists(link_file):
                self._dbg(f"target is binary: found {link_file}")
                self._type |= TargetType.binary
        else:
            raise Exception(f"unknown generator: {gen}")


    @property
    def desc(self):
        return f"[{self.subdir}] {self.name}   [{self._type}]"

    @property
    def is_compiled(self):
        return (self._type & TargetType.binary) != 0

    @property
    def is_intermediate(self):
        return (self._type & TargetType.interm) != 0

    @property
    def output_file(self):
        # TODO this assumes default ouput path.
        # if the project's cmake scripts change the output path,
        # then this logic will fail
        gen = self.build.generator
        if gen.is_msvc:
            f = f"{self.subdir_abs}/{self.build.build_type}/{self.name}.exe"
            return f
        elif gen.is_makefile:
            f = f"{self.subdir_abs}/{self.name}"
            if os.path.exists(f):
                self._dbg(f"found target executable: {f}")
                return f
            else:
                self._dbg(f"could not find standard target executable: {f}")
                fallbacks = (
                    f"{self.build.builddir}/bin/{self.name}",
                )
                for f in fallbacks:
                    self._dbg(f"trying {f}")
                    if os.path.exists(f):
                        self._dbg(f"found target executable: {f}")
                        return f
                    else:
                        self._dbg(f"could not target executable: {f}")
                raise Exception("could not find target executable")
        else:
            raise Exception(f"unknown generator: {gen}")

    @property
    def vcxproj(self):
        assert self.build.generator.is_msvc
        return util.cacheattr(self, "_vcxproj", lambda: vsinfo.VcxProj(self.projfile))

    @property
    def tlog(self):
        "get the arguments for compiling the given source file with Visual Studio"
        assert self.build.generator.is_msvc
        assert self.is_binary
        def get_tlog():
            variant = self.vcxproj.get_variant(str(self.build.build_type), self.build.architecture)
            tlog_dir = util.chkf(f"{variant.intdir}/{target}.tlog")
            tlog = util.chkf(f"{tlog_dir}/CL.command.1.tlog")
            return vsinfo.ClCommandTlog(tlog)
        return util.cacheattr(self, "_tlog", get_tlog)

    def vs_cl_cmd(self, source_file):
        "get the arguments for compiling the given source file with Visual Studio"
        abspath = os.path.join(self.build.projdir, source_file)
        cl_cmd = self.tlog.get_cmd_line(abspath)
        cxx_compiler = self.build.cxx_compiler
        cl_cmd = " ".join(shlex.split(f'"{cxx_compiler}" {cl_cmd}', posix=False))
        dev_cmd = " ".join(self.build.vs_dev_cmd(target))
        return f"{dev_cmd} {cl_cmd}"
