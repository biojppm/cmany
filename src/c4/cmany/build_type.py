from .build_item import BuildItem


# -----------------------------------------------------------------------------
class BuildType(BuildItem):
    """Specifies a build type, ie, one of Release, Debug, etc"""

    @staticmethod
    def default_str():
        return "Release"

    @staticmethod
    def default(toolchain: str=None):
        return BuildType(__class__.default_str())
