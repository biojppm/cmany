
from collections import OrderedDict as odict

class CFlag:

    def __init__(self, name, gcc, clang, icc, vs, expl):
        self.name = name
        self.expl = expl
        self.gcc = gcc
        self.clang = clang
        self.icc = icc
        self.vs = vs

def _f(name, gcc, clang, icc, vs, expl):
        return name, CompileOption(name, gcc, clang, icc, vs, expl)

known_flags = odict([
    #    name                   gcc                                  clang                                icc                                  vs                                  explanation
    _f('cpp11'              , '-std=c++11'                       , '-std=c++11'                       , '-std=c++11'                       , ''                                , 'enable C++11 mode'),  # nopep8
    _f('cpp14'              , '-std=c++14'                       , '-std=c++14'                       , '-std=c++14'                       , ''                                , 'enable C++14 mode'),  # nopep8
    _f('cpp1z'              , '-std=c++1z'                       , '-std=c++1z'                       , '-std=c++1z'                       , ''                                , 'enable C++1z mode'),  # nopep8
    _f('thread'             , '-pthread'                         , '-pthread'                         , '-pthread'                         , ''                                , 'enable threads'),  # nopep8
    _f('wall'               , '-Wall'                            , '-Wall'                            , '-Wall'                            , '/Wall'                           , 'enable full warnings'),  # nopep8
    _f('pedantic'           , '-Wpedantic'                       , '-Wpedantic'                       , '-Wpedantic'                       , '/W4'                             , 'compile in pedantic mode'),  # nopep8
    _f('strict_aliasing'    , '-fstrict-aliasing'                , '-fstrict-aliasing'                , '-fstrict-aliasing'                , ''                                , 'enable strict aliasing'),  # nopep8
    _f('no_strict_aliasing' , '-fno-strict-aliasing'             , '-fno-strict-aliasing'             , '-fno-strict-aliasing'             , ''                                , 'disable strict aliasing'),  # nopep8
    _f('fast_math'          , '-ffast-math'                      , '-ffast-math'                      , '-ffast-math'                      , '/fp:fast /Qfast_transcendentals' , 'enable fast math http://stackoverflow.com/a/22135559'),  # nopep8
    _f('no_rtti'            , '-fno-rtti'                        , '-fno-rtti'                        , '-fno-rtti'                        , '/GR-'                            , 'disable run-time type information'),  # nopep8
    _f('no_exceptions'      , '-fno-exceptions'                  , '-fno-exceptions'                  , '-fno-exceptions'                  , '/EHsc-'                          , 'disable exceptions'),  # nopep8
    _f('no_stdlib'          , '-fnostdlib'                       , '-fnostdlib'                       , '-fnostdlib'                       , '/NODEFAULTLIB'                   , 'disable standard library'),  # nopep8
    _f('static_stdlib'      , '-static-libstdc++ -static-libgcc' , '-static-libstdc++ -static-libgcc' , '-static-libstdc++ -static-libgcc' , '/MD'                             , 'link statically with the standard library http://stackoverflow.com/questions/13636513/linking-libstdc-statically-any-gotchas'),  # nopep8
    _f('lto'                , '-flto'                            , '-flto'                            , '-flto'                            , '/GL'                             , 'enable whole program optimization'),  # nopep8
    _f('g'                  , '-g'                               , '-g'                               , '-g'                               , '/Zi'                             , 'add debug information'),  # nopep8
    _f('g3'                 , '-g3'                              , '-g3'                              , '-g3'                              , '/Zi'                             , 'add full debug information'),  # nopep8
    _f('no_bufsec'          , ''                                 , ''                                 , ''                                 , '/GS-'                            , 'disable buffer security checks'),  # nopep8
    _f('o2'                 , '-O2'                              , '-O2'                              , '-O2'                              , '/O2'                             , 'optimize level 2'), # nopep8
    _f('o3'                 , '-O3'                              , '-O3'                              , '-O3'                              , '/Ox'                             , 'optimize level 3'), # nopep8
    _f('os'                 , '-Os'                              , '-Os'                              , '-Os'                              , '/Os'                             , 'optimize for size'),  # nopep8
    _f('ofast'              , '-Ofast'                           , '-Ofast'                           , '-Ofast'                           , '/Ot'                             , 'optimize for speed'), # nopep8
    _f('onative'            , '-march=native'                    , '-march=native'                    , '-march=native'                    , ''                                , 'optimize for native architecture'), # nopep8
    _f('sse'                , '-msse'                            , '-msse'                            , '-msse'                            , '/arch:sse'                       , 'enable SSE instructions'), # nopep8
    _f('sse2'               , '-msse2'                           , '-msse2'                           , '-msse2'                           , '/arch:sse2'                      , 'enable SSE2 instructions'), # nopep8
    _f('avx'                , '-mavx'                            , '-mavx'                            , '-mavx'                            , '/arch:avx'                       , 'enable AVX instructions'), # nopep8
    _f('avx2'               , '-mavx2'                           , '-mavx2'                           , '-mavx2'                           , '/arch:avx2'                      , 'enable AVX2 instructions'), # nopep8
])

del _f


def get(name, compiler=None):
    opt = known_flags.get(name)
    if opt is None:
        raise Exception("could not find compile option preset: " + name)
    if compiler is not None:
        if hasattr(opt, compiler.shortname):
            return getattr(opt, compiler.shortname)
        return ''
    return opt

