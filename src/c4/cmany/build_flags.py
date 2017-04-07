from .named_item import NamedItem as NamedItem
from . import flags as c4flags


# -----------------------------------------------------------------------------
class BuildFlags(NamedItem):

    def __init__(self, name, compiler=None, **kwargs):
        super().__init__(name)
        self.cmake_vars = kwargs.get('vars', [])
        self.defines = kwargs.get('defines', [])
        self.cflags = kwargs.get('cflags', [])
        self.cxxflags = kwargs.get('cxxflags', [])
        # self.include_dirs = kwargs['include_dirs']
        # self.link_dirs = kwargs['link_dirs']
        if compiler is not None:
            self.resolve_flag_aliases(compiler)

    def resolve_flag_aliases(self, compiler):
        self.defines = c4flags.as_defines(self.defines, compiler)
        self.cflags = c4flags.as_flags(self.cflags, compiler)
        self.cxxflags = c4flags.as_flags(self.cxxflags, compiler)

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

    def log(self, log_fn=print, msg=""):
        t = "BuildFlags[{}]: {}".format(self.name, msg)
        log_fn(t, "cmake_vars=", self.cmake_vars)
        log_fn(t, "defines=", self.defines)
        log_fn(t, "cxxflags=", self.cxxflags)
        log_fn(t, "cflags=", self.cflags)
