
import re
import os

from collections import OrderedDict as odict

from .conf import CMANY_DIR
from .util import cacheattr, setcwd, runsyscmd

def getcachevar(builddir, var):
    v = getcachevars(builddir, [var])
    return v[var]

def getcachevars(builddir, varlist):
    vlist = [v + ':' for v in varlist]
    values = odict()
    rx = r'^(.*?):.*?=(.*)$'
    with setcwd(builddir, silent=True):
        with open('CMakeCache.txt') as f:
            for line in f:
                for v in vlist:
                    if line.startswith(v):
                        ls = line.strip()
                        vt = re.sub(rx, r'\1', ls)
                        values[vt] = re.sub(rx, r'\2', ls)
    return values


# -----------------------------------------------------------------------------
class CMakeSysInfo:
    """encapsulates the results returned from
    `cmake [-G <which_generator>] --system-information`.
    This is used for selecting default values for system, compiler,
    generator, etc."""

    @staticmethod
    def generator():
        return cacheattr(__class__, '_generator_default',
                         lambda: __class__._getstr('CMAKE_GENERATOR', 'default'))

    @staticmethod
    def system_name(which_generator="default"):
        return cacheattr(__class__, '_system_name_' + which_generator,
                         lambda: __class__._getstr('CMAKE_SYSTEM_NAME', which_generator).lower())

    @staticmethod
    def architecture(which_generator="default"):
        return cacheattr(__class__, '_architecture_' + which_generator,
                         lambda: __class__._getstr('CMAKE_SYSTEM_PROCESSOR', which_generator).lower())

    @staticmethod
    def cxx_compiler(which_generator="default"):
        return cacheattr(__class__, '_cxx_compiler_' + which_generator,
                         lambda: __class__._getpath('CMAKE_CXX_COMPILER', which_generator))

    @staticmethod
    def c_compiler(which_generator="default"):
        return cacheattr(__class__, '_c_compiler_' + which_generator,
                         lambda: __class__._getpath('CMAKE_C_COMPILER', which_generator))

    @staticmethod
    def info(which_generator="default"):
        return cacheattr(__class__, '_info' + which_generator,
                         lambda: __class__.system_info(which_generator))

    @staticmethod
    def _getpath(var_name, which_generator):
        s = __class__._getstr(var_name, which_generator)
        # s = re.sub(r'\\', '/', s)
        return s

    @staticmethod
    def _getstr(var_name, which_generator):
        regex = r'^' + var_name + r' "(.*)"'
        for l in __class__.info(which_generator):
            if l.startswith(var_name):
                l = l.strip("\n").lstrip(" ").rstrip(" ")
                # print(var_name, "startswith :", l)
                if re.match(regex, l):
                    s = re.sub(regex, r'\1', l)
                    # print(var_name, "result: '" + s + "'")
                    return s
        err = "could not find variable {} in the output of `cmake --system-information`"
        raise Exception(err.format(var_name))

    @staticmethod
    def system_info(gen):
        # print("CMakeSystemInfo: asked info for", which_generator)
        p = re.sub(r'[() ]', '_', gen)
        d = os.path.join(CMANY_DIR, 'cmake_info', p)
        p = os.path.join(d, 'info')
        if os.path.exists(p):
            # print("CMakeSystemInfo: asked info for", which_generator, "... found", p)
            with open(p, "r") as f:
                i = f.readlines()
        else:
            if gen == "default":
                cmd = ['cmake', '--system-information']
            else:
                if gen.startswith('vs') or gen.startswith('Visual Studio'):
                    from c4.cmany import vsinfo
                    gen = vsinfo.to_gen(gen)
                cmd = ['cmake', '-G', '"{}"'.format(gen), '--system-information']
            if not os.path.exists(d):
                os.makedirs(d)
            print("\ncmany: CMake information for generator '{}' was not found. Creating and storing...".format(gen))
            with setcwd(d):
                out = runsyscmd(cmd, echo_output=False, capture_output=True)
            print("cmany: finished generating information for generator '{}'\n".format(gen))
            with open(p, "w") as f:
                f.write(out)
            i = out.split("\n")
        return i
