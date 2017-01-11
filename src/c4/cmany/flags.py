
from collections import OrderedDict as odict

from . import util

def _getrealsn(compiler):
    sn = compiler.shortname
    if compiler.is_msvc:
        if compiler.vs.is_clang:
            sn = 'clang'
        else:
            sn = 'vs'
    return sn


class CFlag:

    def __init__(self, name, gcc, clang, icc, vs, expl):
        self.name = name
        self.expl = expl
        self.gcc = gcc
        self.clang = clang
        self.icc = icc
        self.vs = vs

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def get(self, compiler):
        sn = _getrealsn(compiler)
        if hasattr(self, sn):
            s = getattr(self, sn)
        else:
            s = ''
        # print(self, sn, s)
        return s

    def values(self):
        return (self.name, self.gcc, self.clang, self.icc, self.vs)


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

def f(name, gcc, clang, icc, vs, expl):
    return name, CFlag(name, gcc, clang, icc, vs, expl)


known_flags = odict([
    #    name                   gcc                                  clang                                icc                                  vs                                  explanation
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

del f
