import os


class Error(Exception):
    def __init__(self, msg, *args, **kwargs):
        msg = msg.format(*args, **kwargs)
        if not msg:
            msg = "unknown error"
        super().__init__(f"ERROR: {msg}")


class NotImplemented(Error):
    def __init__(self, msg):
        super().__init__(f"not implemented: {msg}")


class VSNotFound(Error):
    def __init__(self, vs_spec, msg=None):
        msg = "" if msg is None else f". {msg}."
        super().__init__(f"Visual Studio not found: {vs_spec}{msg}")


class CompilerNotFound(Error):
    def __init__(self, compiler_spec, msg=None):
        msg = "" if msg is None else f". {msg}."
        super().__init__(f"compiler not found: {compiler_spec}{msg}")


class InvalidGenerator(Error):
    def __init__(self, gen_spec, msg=None):
        msg = "" if msg is None else f". {msg}."
        super().__init__(f"invalid generator: {gen_spec}{msg}")


class NoSupport(Error):
    def __init__(self, feature):
        super().__init__(f"feature not supported: {feature}")


class SubcommandNotFound(Error):
    def __init__(self, cmds, args):
        super().__init__(f"could not find subcommand {cmds} in args {args}")


class UnknownCombinationArg(Error):
    def __init__(self, a):
        super().__init__(f"unknown combination argument: {a}")


class ProjDirNotFound(Error):
    def __init__(self, proj_dir):
        cwd = os.getcwd()
        super().__init__(f"project dir was not found: '{proj_dir}' (curr dir is '{cwd}')")


class CMakeListsNotFound(Error):
    def __init__(self, proj_dir):
        super().__init__(f"CMakeLists.txt or CMakeCache.txt not found at dir: {proj_dir}")


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
