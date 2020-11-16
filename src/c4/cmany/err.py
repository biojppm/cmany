import os


class Error(Exception):
    def __init__(self, msg, *args, **kwargs):
        msg = msg.format(*args, **kwargs)
        if not msg:
            msg = "unknown error"
        super().__init__("ERROR: {}".format(msg))


class VSNotFound(Error):
    def __init__(self, vs_spec, msg=None):
        msg = "" if msg is None else ". {}.".format(msg)
        super().__init__("Visual Studio not found: {}{}", vs_spec, msg)


class CompilerNotFound(Error):
    def __init__(self, compiler_spec, msg=None):
        msg = "" if msg is None else ". {}.".format(msg)
        super().__init__("compiler not found: {}{}", compiler_spec, msg)


class InvalidGenerator(Error):
    def __init__(self, gen_spec, msg=None):
        msg = "" if msg is None else ". {}.".format(msg)
        super().__init__("invalid generator: {}{}", gen_spec, msg)


class NoSupport(Error):
    def __init__(self, feature):
        super().__init__("feature not supported: {}", feature)


class SubcommandNotFound(Error):
    def __init__(self, cmds, args):
        super().__init__("could not find subcommand {} in args {}", cmds, args)


class UnknownCombinationArg(Error):
    def __init__(self, a):
        super().__init__("unknown combination argument:", a)


class ProjDirNotFound(Error):
    def __init__(self, proj_dir):
        if proj_dir is None:
            super().__init__("project dir was not given")
        else:
            msg = "project dir was not found: '{}' (curr dir is '{}')"
            super().__init__(msg, proj_dir, os.getcwd())


class CMakeListsNotFound(Error):
    def __init__(self, proj_dir):
        super().__init__("CMakeLists.txt not found at dir: {}", proj_dir)


class BuildDirNotFound(Error):
    def __init__(self, bdir, purpose=None):
        msg = "{}build dir was not found: '{}' (curr dir is '{}')"
        purpose = "" if purpose is None else "{}: ".format(purpose)
        super().__init__(msg, purpose, bdir, os.getcwd())


class CacheFileNotFound(Error):
    def __init__(self, cfile, bdir, purpose=None):
        msg = "{}cache file not found: '{}' (build dir is '{}' curr dir is '{}')"
        purpose = "" if purpose is None else "{}: ".format(purpose)
        super().__init__(msg, purpose, cfile, bdir, os.getcwd())


class BuildSerializationNotFound(Error):
    def __init__(self, sfile, bdir):
        msg = "build serialization does not exist: '{}' (build dir is '{}', curr dir is '{}')"
        super().__init__(msg, sfile, bdir, os.getcwd())


class ToolchainFileNotFound(Error):
    def __init__(self, tcfile, build):
        msg = "toolchain file not found: {}"
        super().__init__(msg, tcfile)


class ConfigFileNotFound(Error):
    def __init__(self, cfgf):
        msg = "config file not found: {}"
        super().__init__(msg, cfgf)


class FlagAliasNotFound(Error):
    def __init__(self, name, known):
        known = "" if known is None else ". Must be one of {}".format([str(n) for n in known])
        super().__init__("flag alias not found: {}{}", name, known)


class TooManyTargets(Error):
    def __init__(self, generator):
        msg = ("Building multiple targets with this generator is not "
               "implemented. "
               "cmake --build cannot handle multiple --target " +
               "invokations. A generator-specific command must be "
               "written to handle multiple targets with this "
               "generator")
        super().__init__(msg + '("{}")', generator.name)


class BuildError(Error):
    def __init__(self, context, build, cmd, e):
        self.context = context
        self.build = build
        self.cmd = cmd
        self.exc = e
        #super().__init__("{} {}: {}. Command was {}", context, build, e, cmd)
        super().__init__("{} {}: {}", context, build, e)


class ConfigureFailed(BuildError):
    def __init__(self, build, cmd, e):
        super().__init__("failed configure for build", build, cmd, e)


class CompileFailed(BuildError):
    def __init__(self, build, cmd, e):
        super().__init__("failed compile for build", build, cmd, e)


class InstallFailed(BuildError):
    def __init__(self, build, cmd, e):
        super().__init__("failed install for build", build, cmd, e)


class RunCmdFailed(BuildError):
    def __init__(self, build, cmd, e):
        super().__init__("failed command for build", build, cmd, e)
