import re

from .build_item import BuildItem
from . import util


# -----------------------------------------------------------------------------
class Architecture(BuildItem):
    """Specifies a processor architecture"""

    @staticmethod
    def default():
        """return the architecture of the current machine"""
        return Architecture(__class__.default_str())

    @staticmethod
    def default_str():
        # s = CMakeSysInfo.architecture()
        # if s == "amd64":
        #     s = "x86_64"
        # return s
        if util.in_64bit():
            return "x86_64"
        elif util.in_32bit():
            return "x86"

    @property
    def is64(self):
        return util.cacheattr(self, "_is64",
                              lambda: re.search('64', self.name) is not None)

    @property
    def is32(self):
        return not self.is64 and not self.is_arm

    @property
    def is_arm(self):
        return "arm" in self.name.lower()

    @property
    def vs_dev_env_name(self):
        # [arch]: x86 | amd64 | x86_amd64 | x86_arm | x86_arm64 | amd64_x86 | amd64_arm | amd64_arm64
        if self.is_arm:
            raise Exception("not implemented")
        if self.is64:
            return "x64"
        else:
            return "x86"
