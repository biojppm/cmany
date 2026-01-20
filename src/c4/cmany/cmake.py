import re
import os

from glob import glob
from collections import OrderedDict as odict

from .conf import USER_DIR
from .util import cacheattr, setcwd, runsyscmd, chkf
from .util import logdbg as dbg
from . import util
from . import err


def _can_change_cache_type(varname, prevtype, nexttype):
    """when CMAKE_C_COMPILER et al are set in the preload file or from
    the command line, cmake sets the vartype to STRING, so we work
    around that by allowing a change to its proper type of FILEPATH,
    which is the one that would prevail if nothing had been set."""
    if varname.startswith("CMAKE_") and varname.endswith("_COMPILER"):
        if prevtype == "STRING" and nexttype == "FILEPATH":
            return True
    return False


_cache_entry = r'^(.*?)(:.*?)=(.*)$'
def _named_cache_entry(name: str):
    return r'^{}(:.*?)=(.*)$'.format(name)


def hascache(builddir):
    c = os.path.join(builddir, 'CMakeCache.txt')
    if os.path.exists(c):
        return c
    return None


def setcachevars(builddir, varvalues):
    assert os.path.isabs(builddir), builddir
    cachefile = os.path.join(builddir, "CMakeCache.txt")
    if not os.path.exists(cachefile):
        raise err.CacheFileNotFound(cachefile, builddir, "setcachevars")
    with open(cachefile, 'r') as f:
        ilines = f.readlines()
        olines = []
    rx = {}  # save the splits and regular expressions
    for k, v in varvalues.items():
        spl = k.split(':')
        name = spl[0]
        vartype = spl[1] if (len(spl) > 1) else None
        rx[name] = (vartype, v, re.compile(_named_cache_entry(name)))
    for l in ilines:
        for k, (vartype, v, rxname) in rx.items():
            if rxname.match(l):
                dbg("committing: before=", l.strip())
                if vartype is not None:
                    existing_type = re.sub(_cache_entry, r'\2', l)
                    assert existing_type.startswith(':')
                    existing_type = existing_type[1:]
                    existing_type = existing_type.strip("\r\n")
                    if vartype != existing_type:
                        if not _can_change_cache_type(k, existing_type, vartype):
                            raise err.CannotChangeCacheVarType(cachefile, k, existing_type, vartype)
                    n = "{}:{}={}\n".format(k, vartype, v)
                else:
                    n = re.sub(_cache_entry, r'\1\2=' + v, l)
                dbg("committing: after=", n.strip())
                l = n
            olines.append(l)
    with open(cachefile, 'w') as f:
        f.writelines(olines)


def getcachevars(builddir, varlist):
    vlist = [v + ':' for v in varlist]
    values = odict()
    with setcwd(builddir, silent=True):
        if not os.path.exists("CMakeCache.txt"):
            raise err.CacheFileNotFound("CMakeCache.txt", builddir, "getcachevars")
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
                if line.startswith('#'):
                    continue
                if not re.match(_cache_entry, line):
                    continue
                ls = line.strip()
                name = re.sub(_cache_entry, r'\1', ls)
                vartype = re.sub(_cache_entry, r'\2', ls)[1:]
                value = re.sub(_cache_entry, r'\3', ls)
                # dbg("loadvars1", name, vartype, value)
                v[name] = CMakeCacheVar(name, value, vartype, dirty=False, from_input=False)
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
        q = lambda v: "'" + str(v) + "'"
        dbg("setting cache var:", name+':'+str(vartype), "=", q(val), "cache=dirty" if self.dirty else "cache=clean")
        v = self.get(name)
        if v is not None:
            dbg("setting cache var:", name, "was found with", q(v.val))
            if (vartype is not None) and (vartype != v.vartype):
                if not _can_change_cache_type(name, v.vartype, vartype):
                    raise err.CannotChangeCacheVarType(None, v.name, v.vartype, vartype)
            changed = v.reset(val, **kwargs)
            dbg("setting cache var:", name, "changed" if changed else "same value")
            self.dirty |= changed
            return changed
        else:
            dbg("setting cache var:", name, "was not found")
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
            dbg("committing to cache: {}:{}={}".format(v.name, v.vartype, v.val))
            if v.vartype is not None:
                name_and_type = "{}:{}".format(v.name, v.vartype)
            else:
                name_and_type = v.name
            tmp[name_and_type] = v.val
        setcachevars(builddir, tmp)
        for _, v in self.items():
            v.dirty = False
        self.dirty = False
        return True


def _guess_var_type(name, val):
    """make an informed guess of the var type"""
    # first look at the name
    uppername = name.upper()
    if (("-ADVANCED" in uppername) or
        (uppername.startswith("CMAKE_") and (uppername in (
            "CMAKE_CACHEFILE_DIR",
            "CMAKE_CACHE_MAJOR_VERSION",
            "CMAKE_CACHE_MINOR_VERSION",
            "CMAKE_CACHE_PATCH_VERSION",
            "CMAKE_CACHE_PATCH_VERSION",
            "CMAKE_COMMAND",
            "CMAKE_CPACK_COMMAND",
            "CMAKE_CTEST_COMMAND",
            "CMAKE_EDIT_COMMAND",
            "CMAKE_EXECUTABLE_FORMAT",
            "CMAKE_EXTRA_GENERATOR",
            "CMAKE_GENERATOR",
            "CMAKE_GENERATOR_INSTANCE",
            "CMAKE_GENERATOR_PLATFORM",
            "CMAKE_GENERATOR_TOOLSET",
            "CMAKE_HOME_DIRECTORY",
            "CMAKE_INSTALL_SO_NO_EXE",
            "CMAKE_NUMBER_OF_MAKEFILES",
            "CMAKE_PLATFORM_INFO_INITIALIZED",
            "CMAKE_ROOT",
            "CMAKE_UNAME",
        ))) or
        (uppername.startswith("_CMAKE"))):
        return "INTERNAL"
    elif uppername in (
            "CMAKE_EXPORT_COMPILE_COMMANDS",
            "CMAKE_SKIP_RPATH",
            "CMAKE_SKIP_INSTALL_RPATH",
    ):
        return "BOOL"
    elif (uppername in (
            "CMAKE_FIND_PACKAGE_REDIRECTS_DIR",
            "CMAKE_PROJECT_DESCRIPTION",
            "CMAKE_PROJECT_HOMEPAGE_URL",
            "CMAKE_PROJECT_NAME",
    ) or (
        uppername.endswith("_BINARY_DIR")
        or uppername.endswith("_IS_TOP_LEVEL")
        or uppername.endswith("_SOURCE_DIR")
    )):
        return "STATIC"
    elif (
          ("PATH" in uppername) or
          uppername.endswith("COMPILER") or
          uppername.endswith("COMPILER_AR") or
          uppername.endswith("COMPILER_RANLIB") or
          uppername.endswith("DLLTOOL") or
          uppername.endswith("LINKER")
    ):
        return "FILEPATH"
    #
    # now look at the value
    upperval = val.upper()
    if upperval in (
        "ON", "OFF", "NO", "YES", "1", "0",
        "TRUE", "FALSE", "T", "F", "N", "Y",
    ):
        # https://cmake.org/pipermail/cmake/2007-December/018548.html
        return "BOOL"
    elif os.path.isfile(val):
        return "FILEPATH"
    elif os.path.isdir(val) or "DIR" in name.upper() or os.path.isabs(val):
        return "PATH"
    else:
        return "STRING"


# -------------------------------------------------------------------------
class CMakeCacheVar:

    def __init__(self, name, val, vartype=None, dirty=False, from_input=False):
        self.name = name
        self.val = val
        self.vartype = vartype if vartype else _guess_var_type(name, val)
        self.dirty = dirty
        self.from_input = from_input

    def reset(self, val, **kwargs):
        """
        :param val:
        :param kwargs:
            force_dirty, defaults to False
            from_input, defaults to None
        :return:
        """
        dbg("setting cache var:", self.name, "'{}' to '{}'".format(self.val, val), "(dirty={})".format(self.dirty))
        dbg("setting cache var:", self.name, "kwargs=", kwargs)
        force_dirty = kwargs.get('force_dirty', False)
        from_input = kwargs.get('from_input')
        if kwargs.get("vartype") is not None:
            if not _can_change_cache_type(self.name, self.vartype, kwargs.get("vartype")):
                raise err.CannotChangeCacheVarType(None, self.name, self.vartype, kwargs.get("vartype"))
        if from_input is not None:
            self.from_input = from_input
        if self.vartype == 'STRING':
            dbg("setting cache var:", self.name, "is string")
            candidates = (val, val.strip("'"), val.strip('"'))
            equal = False
            for c in candidates:
                if c == self.val:
                    dbg("setting cache var:", self.name, "is string equal to", c)
                    equal = True
                    break
        else:
            equal = (self.val == val)
            dbg("setting cache var:", self.name, "is", "equal" if equal else "NOT equal")
        if not equal:
            dbg("setting cache var:", self.name, "CHANGE!")
            self.val = val
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
