from .named_item import NamedItem as NamedItem

from . import util
from .util import logdbg as dbg
from . import err


# -----------------------------------------------------------------------------
class BuildFlags(NamedItem):

    attrs = ('cmake_vars', 'defines', 'cflags', 'cxxflags', 'toolchain')

    def __init__(self, name, **kwargs):
        super().__init__(name)
        self.cmake_vars = kwargs.get('cmake_vars', [])
        self.defines = kwargs.get('defines', [])
        self.cflags = kwargs.get('cflags', [])
        self.cxxflags = kwargs.get('cxxflags', [])
        self.toolchain = kwargs.get('toolchain')
        # self.include_dirs = kwargs['include_dirs']
        # self.link_dirs = kwargs['link_dirs']

    def empty(self):
        if self.cmake_vars:
            return False
        if self.defines:
            return False
        if self.cflags:
            return False
        if self.cxxflags:
            return False
        if self.toolchain:
            return False
        return True

    def resolve_flag_aliases(self, compiler, aliases):
        self.defines = aliases.as_defines(self.defines, compiler)
        self.cflags = aliases.as_flags(self.cflags, compiler)
        self.cxxflags = aliases.as_flags(self.cxxflags, compiler)

    def append_flags(self, other, append_to_name=True):
        """other will take precedence, ie, their options will come last"""
        if append_to_name and other.name:
            self.name += '_' + other.name
        self.cmake_vars += other.cmake_vars
        self.defines += other.defines
        self.cflags += other.cflags
        self.cxxflags += other.cxxflags
        # self.include_dirs += other.include_dirs
        # self.link_dirs += other.link_dirs
        self.toolchain = __class__.merge_toolchains(self.toolchain, other.toolchain)

    def log(self, log_fn=print, msg=""):
        t = "BuildFlags[{}]: {}".format(self.name, msg)
        log_fn(t, "cmake_vars=", self.cmake_vars)
        log_fn(t, "defines=", self.defines)
        log_fn(t, "cxxflags=", self.cxxflags)
        log_fn(t, "cflags=", self.cflags)
        log_fn(t, "toolchain=", self.toolchain)

    @staticmethod
    def merge_toolchains(tc1, tc2):
        dbg("merge_toolchains:", tc1, tc2)
        if ((tc1 != tc2) and ((tc1 is not None) and (tc2 is not None))):
            raise err.Error("conflicting toolchains: {} vs {}", tc1, tc2)
        if tc1 is None and tc2 is not None:
            dbg("picking toolchain:", tc2)
            tc1 = tc2
        return tc1

    def save_config(self, yml_node):
        for n in __class__.attrs:
            a = getattr(self, n)
            if a:
                a = __class__.flag_list_to_str(a)
                yml_node[n] = a

    def load_config(self, yml_node):
        for n in __class__.attrs:
            a = yml_node.get(n)
            if a is not None:
                if n != 'toolchain':
                    a = __class__.flag_str_to_list(a)
                setattr(self, n, a)

    @staticmethod
    def flag_list_to_str(li):
        if isinstance(li, str):
            return li
        return " ".join(li)

    @staticmethod
    def flag_str_to_list(s):
        if isinstance(s, list):
            return s
        return util.splitesc_quoted(s, ' ')
