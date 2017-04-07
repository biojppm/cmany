from .build_item import BuildItem


# -----------------------------------------------------------------------------
class BuildType(BuildItem):
    """Specifies a build type, ie, one of Release, Debug, etc"""

    @staticmethod
    def default():
        return BuildType("Release")
