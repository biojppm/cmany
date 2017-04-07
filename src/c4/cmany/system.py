from .build_item import BuildItem
from .cmake import CMakeSysInfo


# -----------------------------------------------------------------------------
class System(BuildItem):
    """Specifies an operating system"""

    @staticmethod
    def default():
        """return the current operating system"""
        return System(__class__.default_str())

    @staticmethod
    def default_str():
        s = CMakeSysInfo.system_name()
        if s == "mac os x" or s == "Darwin":
            s = "mac"
        return s
