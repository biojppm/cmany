import os


class Error(Exception):
    def __init__(self, msg, *args, **kwargs):
        msg = msg.format(*args, **kwargs)
        if not msg:
            msg = "unknown error"
        super().__init__("ERROR: {}".format(msg))


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
