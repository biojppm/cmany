from collections import OrderedDict as odict
from ruamel import yaml
import copy

from . import util

known_compilers = ['gcc', 'clang', 'icc', 'vs']


def _getrealsn(compiler):
    if isinstance(compiler, str):
        return compiler
    sn = compiler.shortname
    if compiler.is_msvc:
        if compiler.vs.is_clang:
            sn = 'clang'
        else:
            sn = 'vs'
    return sn


class CFlag:

    def __init__(self, name, desc='', **kwargs):
        self.name = name
        self.desc = desc
        self.compilers = kwargs.get('compilers', [])
        for k, v in kwargs.items():
            self.set(k, v)

    def get(self, compiler):
        sn = _getrealsn(compiler)
        if hasattr(self, sn):
            s = getattr(self, sn)
        else:
            s = ''
        # print(self, sn, s)
        return s

    def set(self, compiler, val=''):
        sn = _getrealsn(compiler)
        if not sn in self.compilers:
            self.compilers.append(sn)
        setattr(self, sn, val)

    def add_compiler(self, compiler):
        sn = _getrealsn(compiler)
        if not sn in self.compilers:
            self.compilers.append(sn)
        if not hasattr(self, sn):
            self.set(sn)

    def merge_from(self, that):
        for c in that.compilers:
            v = that.get(c)
            self.set(c, v)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


def get(name, compiler=None):
    opt = known_flags.get(name)
    if opt is None:
        raise Exception("could not find compile option preset: " + name)
    if compiler is not None:
        return opt.get(compiler)
    return opt


def as_flags(spec, compiler=None):
    out = []
    for s in spec:
        f = known_flags.get(s)
        if f is not None:
            out.append(f)
        else:
            out.append(CFlag(s, s, s, s, s, ''))
    return out


def as_defines(spec, compiler=None):
    out = []
    wf = '/D' if _getrealsn(compiler) == 'vs' else '-D'
    for s in spec:
        out.append(wf)
        out.append(s)
    return out


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

def f(name, gcc=None, clang=None, icc=None, vs=None, desc=None):
    return name, CFlag(name, desc, gcc=gcc, clang=clang, icc=icc, vs=vs)

known_flags = odict([
    #    name                   gcc                                  clang                                icc                                  vs                                  desc
    f('c++11'              , '-std=c++11'                       , '-std=c++11'                       , '-std=c++11'                       , ''                                , 'enable C++11 mode'),  # nopep8
    f('c++14'              , '-std=c++14'                       , '-std=c++14'                       , '-std=c++14'                       , ''                                , 'enable C++14 mode'),  # nopep8
    f('c++1z'              , '-std=c++1z'                       , '-std=c++1z'                       , '-std=c++1z'                       , ''                                , 'enable C++1z mode'),  # nopep8
    f('thread'             , '-pthread'                         , '-pthread'                         , '-pthread'                         , ''                                , 'enable threads'),  # nopep8
    f('wall'               , '-Wall'                            , '-Wall'                            , '-Wall'                            , '/Wall'                           , 'enable full warnings'),  # nopep8
    f('pedantic'           , '-Wpedantic'                       , '-Wpedantic'                       , '-Wpedantic'                       , '/W4'                             , 'compile in pedantic mode'),  # nopep8
    f('strict_aliasing'    , '-fstrict-aliasing'                , '-fstrict-aliasing'                , '-fstrict-aliasing'                , ''                                , 'enable strict aliasing'),  # nopep8
    f('no_strict_aliasing' , '-fno-strict-aliasing'             , '-fno-strict-aliasing'             , '-fno-strict-aliasing'             , ''                                , 'disable strict aliasing'),  # nopep8
    f('fast_math'          , '-ffast-math'                      , '-ffast-math'                      , '-ffast-math'                      , '/fp:fast /Qfast_transcendentals' , 'enable fast math http://stackoverflow.com/a/22135559'),  # nopep8
    f('no_rtti'            , '-fno-rtti'                        , '-fno-rtti'                        , '-fno-rtti'                        , '/GR-'                            , 'disable run-time type information'),  # nopep8
    f('no_exceptions'      , '-fno-exceptions'                  , '-fno-exceptions'                  , '-fno-exceptions'                  , '/EHsc-'                          , 'disable exceptions'),  # nopep8
    f('no_stdlib'          , '-fnostdlib'                       , '-fnostdlib'                       , '-fnostdlib'                       , '/NODEFAULTLIB'                   , 'disable standard library'),  # nopep8
    f('static_stdlib'      , '-static-libstdc++ -static-libgcc' , '-static-libstdc++ -static-libgcc' , '-static-libstdc++ -static-libgcc' , '/MD'                             , 'link statically with the standard library http://stackoverflow.com/questions/13636513/linking-libstdc-statically-any-gotchas'),  # nopep8
    f('lto'                , '-flto'                            , '-flto'                            , '-flto'                            , '/GL'                             , 'enable whole program optimization'),  # nopep8
    f('g'                  , '-g'                               , '-g'                               , '-g'                               , '/Zi'                             , 'add debug information'),  # nopep8
    f('g3'                 , '-g3'                              , '-g3'                              , '-g3'                              , '/Zi'                             , 'add full debug information'),  # nopep8
    f('no_bufsec'          , ''                                 , ''                                 , ''                                 , '/GS-'                            , 'disable buffer security checks'),  # nopep8
    f('O2'                 , '-O2'                              , '-O2'                              , '-O2'                              , '/O2'                             , 'optimize level 2'), # nopep8
    f('O3'                 , '-O3'                              , '-O3'                              , '-O3'                              , '/Ox'                             , 'optimize level 3'), # nopep8
    f('Os'                 , '-Os'                              , '-Os'                              , '-Os'                              , '/Os'                             , 'optimize for size'),  # nopep8
    f('Ofast'              , '-Ofast'                           , '-Ofast'                           , '-Ofast'                           , '/Ot'                             , 'optimize for speed'), # nopep8
    f('Onative'            , '-march=native'                    , '-march=native'                    , '-march=native'                    , ''                                , 'optimize for native architecture'), # nopep8
    f('sse'                , '-msse'                            , '-msse'                            , '-msse'                            , '/arch:sse'                       , 'enable SSE instructions'), # nopep8
    f('sse2'               , '-msse2'                           , '-msse2'                           , '-msse2'                           , '/arch:sse2'                      , 'enable SSE2 instructions'), # nopep8
    f('avx'                , '-mavx'                            , '-mavx'                            , '-mavx'                            , '/arch:avx'                       , 'enable AVX instructions'), # nopep8
    f('avx2'               , '-mavx2'                           , '-mavx2'                           , '-mavx2'                           , '/arch:avx2'                      , 'enable AVX2 instructions'), # nopep8
])


def dump_yml(comps, flags):
    """dump the given compilers and flags pair into a yml string"""
    txt = ""
    txt += 'compilers: ' + yaml.dump(comps)
    txt += '---\n'
    for n, f in flags.items():
        txt += n + ':\n'
        if f.desc:
            txt += '    desc: ' + f.desc + '\n'
        for comp in comps:
            a = getattr(f, comp)
            a = a if a else "''"
            txt += '    ' + comp + ': ' + a + '\n'
    return txt


def load_yml(txt):
    """load a yml txt into a compilers, flags pair"""
    comps = []
    flags = odict()
    dump = list(yaml.load_all(txt, yaml.RoundTripLoader))
    if len(dump) != 2:
        msg = 'There must be two yaml documents. Did you forget to use --- to separate the compiler list from the flags?'
        raise Exception(msg)
    comps, fs = dump
    comps = list(comps['compilers'])
    #print("load yml: compilers=", comps)
    flags0 = odict(fs)
    for n, yf in flags0.items():
        f = CFlag(n)
        #print("load yml: flag compilers=", f.compilers)
        for comp, val in yf.items():
            if comp == 'desc':
                f.desc = val
            else:
                f.set(comp, val)
            #print("load yml: flag value for", comp, ":", val, "--------->", f.get(comp))
        flags[n] = f
    return comps, flags


def save(comps, flags, filename):
    """save the given compilers and flags into a yml file"""
    yml = dump_yml(comps, flags)
    with open(filename, 'w') as f:
        f.write(yml)


def load(filename):
    with open(filename, 'r') as f:
        txt = f.read()
        comps, flags = load_yml(txt)
        return comps, flags


def merge(comps=None, flags=None, into_comps=None, into_flags=None):
    """merge a compilers and flags pair into a previously existing compilers and flags pair"""
    into_comps = into_comps if into_comps is not None else known_compilers
    into_flags = into_flags if into_flags is not None else known_flags
    result_comps = into_comps
    result_flags = into_flags
    if comps:
        result_comps = copy.deepcopy(into_comps)
        for c in comps:
            if not c in into_comps:
                result_comps.append(c)
    if flags:
        result_flags = copy.deepcopy(into_flags)
        for k, v in flags.items():
            if k in result_flags:
                result_flags[k].merge_from(v)
            else:
                result_flags[k] = copy.deepcopy(v)
                for c in result_comps:
                    result_flags[k].add_compiler(c)
    return result_comps, result_flags


def load_and_merge(filename, into_comps=None, into_flags=None):
    comps, flags = load(filename)
    return merge(comps, flags, into_comps, into_flags)
