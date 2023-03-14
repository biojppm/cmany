import re
import os

from glob import glob
from collections import OrderedDict as odict

from .conf import USER_DIR
from .util import cacheattr, setcwd, runsyscmd, chkf
from .util import logdbg as dbg
from . import util
from . import err

_cache_entry = r'^(.*?)(:.*?)=(.*)$'


def hascache(builddir):
    c = os.path.join(builddir, 'CMakeCache.txt')
    if os.path.exists(c):
        return c
    return None


def setcachevar(builddir, var, value):
    setcachevars(builddir, odict([(var, value)]))


def getcachevar(builddir, var):
    v = getcachevars(builddir, [var])
    return v[var]


def setcachevars(builddir, varvalues):
    with setcwd(builddir, silent=True):
        with open('CMakeCache.txt', 'r') as f:
            ilines = f.readlines()
            olines = []
        for l in ilines:
            for k, v in varvalues.items():
                if l.startswith(k + ':'):
                    n = re.sub(_cache_entry, r'\1\2=' + v, l)
                    l = n
            olines.append(l)
        with open('CMakeCache.txt', 'w') as f:
            f.writelines(olines)


def getcachevars(builddir, varlist):
    vlist = [v + ':' for v in varlist]
    values = odict()
    with setcwd(builddir, silent=True):
        with open('CMakeCache.txt') as f:
            for line in f:
                for v in vlist:
                    if line.startswith(v):
                        ls = line.strip()
                        vt = re.sub(_cache_entry, r'\1', ls)
                        values[vt] = re.sub(_cache_entry, r'\3', ls)
    return values


def loadvars(builddir):
    """if builddir does not exist or does not have a cache, returns an
    empty odict"""
    v = odict()
    if builddir is None or not os.path.exists(builddir):
        return v
    c = os.path.join(builddir, 'CMakeCache.txt')
    if os.path.exists(c):
        with open(c, 'r') as f:
            for line in f:
                # dbg("loadvars0", line.strip())
                if not re.match(_cache_entry, line):
                    continue
                ls = line.strip()
                name = re.sub(_cache_entry, r'\1', ls)
                vartype = re.sub(_cache_entry, r'\2', ls)[1:]
                value = re.sub(_cache_entry, r'\3', ls)
                # dbg("loadvars1", name, vartype, value)
                v[name] = CMakeCacheVar(name, value, vartype)
    return v


def get_cxx_compiler(builddir):
    cmkf = chkf(builddir, "CMakeFiles")
    expr = f"{cmkf}/*/CMakeCXXCompiler.cmake"
    files = glob(expr)
    if len(files) != 1:
        raise Exception(f"could not find compiler settings: {expr}")
    cxxfile = files[0]
    dbg("")
    with open(cxxfile) as f:
        lines = f.readlines()
        lookup = "set(CMAKE_CXX_COMPILER "
        for line in [l.strip() for l in lines]:
            if not line.startswith(lookup):
                continue
            return line[(len(lookup)+1):-2]
    raise Exception("could not find compiler spec")


# -----------------------------------------------------------------------------
class CMakeCache(odict):

    def __init__(self, builddir=None):
        super().__init__(loadvars(builddir))
        self.dirty = False
        self.cache_file = None
        if builddir:
            self.cache_file = os.path.join(builddir, 'CMakeCache.txt')

    def __eq__(self, other):
        """code quality checkers complain that this class adds attributes
        without overriding __eq__. So just fool them!"""
        return super().__eq__(other)

    def getvars(self, names):
        out = odict()
        for n in names:
            v = self.get(n)
            out[n] = v
        return out

    def b(self, name, val, **kwargs):
        """set a boolean"""
        return self.setvar(name, val, "BOOL", **kwargs)

    def s(self, name, val, **kwargs):
        """set a string"""
        return self.setvar(name, val, "STRING", **kwargs)

    def p(self, name, val, **kwargs):
        """set a path to a dir"""
        if util.in_windows():
            val = re.sub(r'\\', r'/', val)
        return self.setvar(name, val, "PATH", **kwargs)

    def f(self, name, val, **kwargs):
        """set a path to a file"""
        if util.in_windows():
            val = re.sub(r'\\', r'/', val)
        return self.setvar(name, val, "FILEPATH", **kwargs)

    def i(self, name, val, **kwargs):
        """set a cmake internal var"""
        return self.setvar(name, val, "INTERNAL", **kwargs)

    def setvar(self, name, val, vartype=None, **kwargs):
        v = self.get(name)
        if v is not None:
            changed = v.reset(val, vartype, **kwargs)
            self.dirty |= changed
            return changed
        else:
            v = CMakeCacheVar(name, val, vartype, dirty=True, **kwargs)
            self[name] = v
            self.dirty = True
            return True

    def commit(self, builddir):
        if (not self.dirty
            or builddir is None
            or not os.path.exists(builddir)
            or not os.path.exists(os.path.join(builddir, 'CMakeCache.txt'))):
            return False
        tmp = odict()
        for _, v in self.items():
            if not v.dirty:
                continue
            tmp[v.name] = v.val
        setcachevars(builddir, tmp)
        for _, v in self.items():
            v.dirty = False
        self.dirty = False
        return True


# -------------------------------------------------------------------------
class CMakeCacheVar:

    def __init__(self, name, val, vartype=None, dirty=False, from_input=False):
        self.name = name
        self.val = val
        self.vartype = self._guess_var_type(name, val, vartype)
        self.dirty = dirty
        self.from_input = from_input

    def _guess_var_type(self, name, val, vartype):
        """make an informed guess of the var type
        @todo: add a test for this"""
        if vartype is not None:
            return vartype
        elif val.upper() in ("ON", "OFF", "NO", "YES", "1", "0", "TRUE", "FALSE", "T", "F", "N", "Y"):
            # https://cmake.org/pipermail/cmake/2007-December/018548.html
            return "BOOL"
        elif os.path.isfile(val) or "PATH" in name.upper():
            return "FILEPATH"
        elif os.path.isdir(val) or "DIR" in name.upper() or os.path.isabs(val):
            return "PATH"
        else:
            return "STRING"

    def reset(self, val, vartype='', **kwargs):
        """
        :param val:
        :param vartype:
        :param kwargs:
            force_dirty, defaults to False
            from_input, defaults to None
        :return:
        """
        force_dirty = kwargs.get('force_dirty', False)
        from_input = kwargs.get('from_input')
        if from_input is not None:
            self.from_input = from_input
        if vartype == 'STRING' or (vartype is None and self.vartype == 'STRING'):
            candidates = (val, val.strip("'"), val.strip('"'))
            equal = False
            for c in candidates:
                if c == self.val:
                    equal = True
                    break
        else:
            equal = (self.val == val)
        if not equal or (vartype is not None and vartype != self.vartype):
            self.val = val
            self.vartype = vartype if vartype is not None else self.vartype
            self.dirty = True
            return True
        if force_dirty:
            self.dirty = True
        return force_dirty

    def __repr__(self):
        return self.name + ':' + self.vartype + '=' + self.val

    def __str__(self):
        return self.name + ':' + self.vartype + '=' + self.val


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class CMakeSysInfo:
    """encapsulates the results returned from
    `cmake [-G <which_generator>][-T <toolset>][-A <architecture>] --system-information`.
    This is used for selecting default values for system, compiler,
    generator, etc."""

    @staticmethod
    def generator(toolchain=None):
        return cacheattr(__class__, '_generator_default',
                         lambda: __class__._getstr('CMAKE_GENERATOR', 'default', toolchain))

    @staticmethod
    def system_name(generator="default", toolchain=None):
        return __class__.var('CMAKE_SYSTEM_NAME', generator, toolchain,
                             lambda v: v.lower())

    @staticmethod
    def architecture(generator="default", toolchain=None):
        return __class__.var('CMAKE_SYSTEM_PROCESSOR', generator, toolchain,
                             lambda v: v.lower())

    @staticmethod
    def cxx_compiler(generator="default", toolchain=None):
        return __class__.var('CMAKE_CXX_COMPILER', generator, toolchain)

    @staticmethod
    def c_compiler(generator="default", toolchain=None):
        return __class__.var('CMAKE_C_COMPILER', generator, toolchain)

    @staticmethod
    def var(var_name, generator="default", toolchain=None, transform_fn=lambda x: x):
        attrname = '_{}_{}'.format(var_name, _gentc_id(generator, toolchain))
        return cacheattr(__class__, attrname,
                         lambda: transform_fn(__class__._getstr(var_name, generator, toolchain)))

    @staticmethod
    def info(generator="default", toolchain=None):
        return cacheattr(__class__, '_info_' + _gentc_id(generator, toolchain),
                         lambda: __class__.system_info(generator, toolchain))

    @staticmethod
    def _getstr(var_name, generator, toolchain):
        regex = r'^{} "(.*)"'.format(var_name)
        for l in __class__.info(generator, toolchain):
            #dbg(l.strip("\n"), l.startswith(var_name), var_name)
            if l.startswith(var_name):
                l = l.strip("\n").lstrip(" ").rstrip(" ")
                #dbg(var_name, "startswith :", l)
                if re.match(regex, l):
                    s = re.sub(regex, r'\1', l)
                    #dbg(var_name, "result: '" + s + "'")
                    return s
        #dbg("--------------------------------------\n", __class__.info(generator))
        raise err.Error("could not find variable {} in the output of `cmake --system-information -G '{}'`",
                        var_name, generator)

    @staticmethod
    def system_info(gen, toolchain_file=None):
        """gen can be a string or a cmany.Generator object"""
        dbg("CMakeSystemInfo: asked info for", gen,
            (("toolchain="+toolchain_file) if toolchain_file is not None else ""))
        toolchain_args = []
        if toolchain_file is not None:
            if not os.path.exists(toolchain_file):
                raise err.ToolchainFileNotFound(toolchain_file)
            toolchain_args = ['--toolchain', toolchain_file]
        d = _geninfodir(gen, toolchain_file)
        p = os.path.join(d, 'cmake_system_information')
        dbg("CMakeSystemInfo: dir=", d)
        dbg("CMakeSystemInfo: path=", p)
        if os.path.exists(p):
            dbg('CMakeSystemInfo: found at', p)
            if util.time_since_modification(p).months >= 1:
                dbg("CMakeSystemInfo: older than 1 month. Refreshing", p)
            else:
                dbg("CMakeSystemInfo: less than 1 month. Choosing", p)
                return _getnfo(p)
        gen_args = []
        from . import generator
        if gen is None:
            dbg("CMakeSystemInfo: gen is None! picking default'")
        elif isinstance(gen, str) and (gen == "default" or gen == ""):
            dbg("CMakeSystemInfo: default! '{}'".format(gen))
        elif isinstance(gen, generator.Generator):
            gen_args = gen.configure_args()
            dbg("CMakeSystemInfo: from generator! '{}' ---> {}".format(gen, gen_args))
        else:
            dbg("CMakeSystemInfo: assume vs! '{}'".format(gen))
            from . import vsinfo
            gen = vsinfo.to_gen(gen)
            if isinstance(gen, list):
                gen_args = ['-G'] + gen
            else:
                if not (gen.startswith('vs') or gen.startswith('Visual Studio')):
                    raise Exception("unknown generator: {}".format(gen))
                gen_args = ['-G', gen]
        cmd = ['cmake'] + toolchain_args + gen_args + ['--system-information', os.path.basename(p)]
        dbg("CMakeSystemInfo: cmd={}".format(cmd))
        # remove export build commands as cmake reacts badly to it,
        # generating an empty info string
        _remove_invalid_args_from_sysinfo_cmd(cmd)
        dbg("CMakeSystemInfo: filtered cmd={}".format(cmd))
        print("\ncmany: CMake information for generator '{}' was not found. Creating and storing... cmd={}".format(gen, cmd))
        #
        if not os.path.exists(d):
            os.makedirs(d)
        with util.setcwd(d):
            runsyscmd(cmd)
        out = _getnfo(p)
        dbg("cmany: finished generating information for generator '{}', cmd={}. Info=\n{}".format(gen, cmd, '\n'.join(out)))
        if not out:
            from .err import InvalidGenerator
            raise InvalidGenerator(gen, "for --system-information. cmd='{}'".format(cmd))
        return out


def _getnfo(p):
    dbg("CMakeSystemInfo: loading=", p)
    if not os.path.exists(p):
        raise FileNotFoundError(p)
    with open(p, "r") as f:
        lines = f.readlines()
        if not lines:
            dbg("CMakeSystemInfo: info for gen", gen, "is empty...", p)
        lines = [l.strip() for l in lines]
        return lines


def _remove_invalid_args_from_sysinfo_cmd(cmd):
    gotit = None
    # remove compile commands args
    for i, elm in enumerate(cmd):
        if 'CMAKE_EXPORT_COMPILE_COMMANDS' in elm:
            # can't strip out if compile commands is not given as one,
            # because the command will become malformed when we remove
            if elm not in ('-DCMAKE_EXPORT_COMPILE_COMMANDS=ON', '-DCMAKE_EXPORT_COMPILE_COMMANDS=OFF'):
                raise Exception("malformed command")
            gotit = i
    if gotit is not None:
        del cmd[gotit]
    # remove architecture args
    if '-A' in cmd:
        i = cmd.index('-A')
        del cmd[i+1]
        del cmd[i]


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


def _geninfodir(gen, toolchain_file: str):
    dbg('cmakeinfo USER_DIR=', USER_DIR)
    if toolchain_file is None:
        base = USER_DIR
    else:
        id = _toolchainid(toolchain_file)
        base = os.path.join(USER_DIR, 'toolchains', id)
        dbg('cmakeinfo toolchain=', toolchain_file)
        dbg('cmakeinfo toolchain_id=', id)
        dbg('cmakeinfo toolchain_base=', base)
    id = _genid(gen)
    d = os.path.join(base, 'cmake_info', id)
    dbg('cmakeinfo base=', base)
    dbg('cmakeinfo gen_id=', id)
    dbg('cmakeinfo infodir=', d)
    return d


def _toolchaindir(toolchain_file: str):
    id = _toolchainid(toolchain_file)
    base = os.path.join(USER_DIR, 'toolchains', id)
    dbg('cmakeinfo USER_DIR=', USER_DIR)
    return base


def _gentc_id(gen, toolchain):
    if toolchain is None:
        return _genid(gen)
    else:
        return _toolchainid(toolchain) + '_' + _genid(gen)


def _genid(gen):
    if gen is None:
        return "None"
    elif isinstance(gen, str):
        p = gen
    elif isinstance(gen, list):
        p = " ".join(gen)
    else:
        from .generator import Generator
        p = gen.sysinfo_name
    p = re.sub(r'[() ]', '_', p)
    return p


def _toolchainid(toolchain: str):
    id = re.sub(os.sep, '_', toolchain)
    id = re.sub(r'[() +.]', '_', id)
    return id
