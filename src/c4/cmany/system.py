from .build_item import BuildItem
from .cmake import CMakeSysInfo


# -----------------------------------------------------------------------------
class System(BuildItem):
    """Specifies an operating system"""

    @staticmethod
    def default(toolchain_file: str=None):
        """return the current operating system"""
        return System(__class__.default_str(toolchain_file))

    @staticmethod
    def default_str(toolchain_file: str=None):
        s = CMakeSysInfo.system_name(toolchain=toolchain_file)
        if s == "mac os x" or s == "Darwin":
            s = "mac"
        return s
