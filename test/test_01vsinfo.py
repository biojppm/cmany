#!/usr/bin/env python3

import unittest as ut
import os.path

import c4.cmany.util as util
import c4.cmany.vsinfo as vsinfo


_sfx = " Win64" if util.in_64bit() else ""
_arc = "x64" if util.in_64bit() else "Win32"


class Test01VisualStudioInfo(ut.TestCase):

    def test00_instances(self):
        if not util.in_windows():
            return
        for k in vsinfo.order:
            #print("testing visual studio:", k)
            vs = vsinfo.VisualStudioInfo(k)
            self.assertIsInstance(vs.year, int)
            def c(w):
                if not os.path.exists(w):
                    self.fail(vs.name + ": " + w + " does not exist")
            if vs.is_installed:
                print("\nFound", vs.name, "aka", str(vs.gen) + ":", vs.dir)
                for i in ('dir', 'vcvarsall', 'devenv', 'msbuild', 'cxx_compiler', 'c_compiler'):
                    print(i, "----", getattr(vs, i))
                c(vs.dir)
                c(vs.vcvarsall)
                c(vs.devenv)
                c(vs.msbuild)
                c(vs.cxx_compiler)
                c(vs.c_compiler)
            else:
                print("not installed:", k, vs.name)

    def test01_find_any(self):
        if not util.in_windows():
            return
        any = vsinfo.find_any()
        if any is None:
            self.fail("could not find any VS installation")
        self.assertIsNotNone(any)



class Test00VisualStudioAliases(ut.TestCase):
    @staticmethod
    def _test_name_to_gen(a, s):
        sc = vsinfo.to_gen(a)
        if sc != s:
            self.fail(f"{a} should be '{s}' but is '{sc}'")

    def test01_name_to_gen_2022(self):
        c = __class__._test_name_to_gen
        c('vs2022'      , ['Visual Studio 17 2022', '-A', _arc])
        c('vs2022_32'   , ['Visual Studio 17 2022', '-A', 'Win32'])
        c('vs2022_64'   , ['Visual Studio 17 2022', '-A', 'x64'])
        c('vs2022_arm'  , ['Visual Studio 17 2022', '-A', 'ARM'])
        c('vs2022_arm32', ['Visual Studio 17 2022', '-A', 'ARM'])
        c('vs2022_arm64', ['Visual Studio 17 2022', '-A', 'ARM64'])
        c('Visual Studio 17 2022' + _sfx , 'Visual Studio 17 2022' + _sfx )
        c('Visual Studio 17 2022'        , 'Visual Studio 17 2022'        )
        c('Visual Studio 17 2022 Win64'  , 'Visual Studio 17 2022 Win64'  )
        c('Visual Studio 17 2022 ARM'    , 'Visual Studio 17 2022 ARM'    )

    def test01_name_to_gen_2019(self):
        c = __class__._test_name_to_gen
        c('vs2019'      , ['Visual Studio 16 2019', '-A', _arc])
        c('vs2019_32'   , ['Visual Studio 16 2019', '-A', 'Win32'])
        c('vs2019_64'   , ['Visual Studio 16 2019', '-A', 'x64'])
        c('vs2019_arm'  , ['Visual Studio 16 2019', '-A', 'ARM'])
        c('vs2019_arm32', ['Visual Studio 16 2019', '-A', 'ARM'])
        c('vs2019_arm64', ['Visual Studio 16 2019', '-A', 'ARM64'])
        c('Visual Studio 16 2019' + _sfx , 'Visual Studio 16 2019' + _sfx )
        c('Visual Studio 16 2019'        , 'Visual Studio 16 2019'        )
        c('Visual Studio 16 2019 Win64'  , 'Visual Studio 16 2019 Win64'  )
        c('Visual Studio 16 2019 ARM'    , 'Visual Studio 16 2019 ARM'    )

    def test01_name_to_gen_2017(self):
        c = __class__._test_name_to_gen
        c('vs2017'      , 'Visual Studio 15 2017' + _sfx )
        c('vs2017_32'   , 'Visual Studio 15 2017'        )
        c('vs2017_64'   , 'Visual Studio 15 2017 Win64'  )
        c('vs2017_arm'  , 'Visual Studio 15 2017 ARM'    )
        c('Visual Studio 15 2017' + _sfx , 'Visual Studio 15 2017' + _sfx )
        c('Visual Studio 15 2017'        , 'Visual Studio 15 2017'        )
        c('Visual Studio 15 2017 Win64'  , 'Visual Studio 15 2017 Win64'  )
        c('Visual Studio 15 2017 ARM'    , 'Visual Studio 15 2017 ARM'    )

    def test01_name_to_gen_2015(self):
        c = __class__._test_name_to_gen
        c('vs2015'      , 'Visual Studio 14 2015' + _sfx )
        c('vs2015_32'   , 'Visual Studio 14 2015'        )
        c('vs2015_64'   , 'Visual Studio 14 2015 Win64'  )
        c('vs2015_arm'  , 'Visual Studio 14 2015 ARM'    )
        c('Visual Studio 14 2015' + _sfx , 'Visual Studio 14 2015' + _sfx )
        c('Visual Studio 14 2015'        , 'Visual Studio 14 2015'        )
        c('Visual Studio 14 2015 Win64'  , 'Visual Studio 14 2015 Win64'  )
        c('Visual Studio 14 2015 ARM'    , 'Visual Studio 14 2015 ARM'    )

    def test01_name_to_gen_2013(self):
        c = __class__._test_name_to_gen
        c('vs2013'      , 'Visual Studio 12 2013' + _sfx )
        c('vs2013_32'   , 'Visual Studio 12 2013'        )
        c('vs2013_64'   , 'Visual Studio 12 2013 Win64'  )
        c('vs2013_arm'  , 'Visual Studio 12 2013 ARM'    )
        c('Visual Studio 12 2013' + _sfx , 'Visual Studio 12 2013' + _sfx )
        c('Visual Studio 12 2013'        , 'Visual Studio 12 2013'        )
        c('Visual Studio 12 2013 Win64'  , 'Visual Studio 12 2013 Win64'  )
        c('Visual Studio 12 2013 ARM'    , 'Visual Studio 12 2013 ARM'    )

    def test01_name_to_gen_2012(self):
        c = __class__._test_name_to_gen
        c('vs2012'      , 'Visual Studio 11 2012' + _sfx )
        c('vs2012_32'   , 'Visual Studio 11 2012'        )
        c('vs2012_64'   , 'Visual Studio 11 2012 Win64'  )
        c('vs2012_arm'  , 'Visual Studio 11 2012 ARM'    )
        c('Visual Studio 11 2012' + _sfx , 'Visual Studio 11 2012' + _sfx )
        c('Visual Studio 11 2012'        , 'Visual Studio 11 2012'        )
        c('Visual Studio 11 2012 Win64'  , 'Visual Studio 11 2012 Win64'  )
        c('Visual Studio 11 2012 ARM'    , 'Visual Studio 11 2012 ARM'    )

    def test01_name_to_gen_2010(self):
        c = __class__._test_name_to_gen
        c('vs2010'      , 'Visual Studio 10 2010' + _sfx )
        c('vs2010_32'   , 'Visual Studio 10 2010'        )
        c('vs2010_64'   , 'Visual Studio 10 2010 Win64'  )
        c('vs2010_ia64' , 'Visual Studio 10 2010 IA64'   )
        c('Visual Studio 10 2010' + _sfx , 'Visual Studio 10 2010' + _sfx )
        c('Visual Studio 10 2010'        , 'Visual Studio 10 2010'        )
        c('Visual Studio 10 2010 Win64'  , 'Visual Studio 10 2010 Win64'  )
        c('Visual Studio 10 2010 IA64'   , 'Visual Studio 10 2010 IA64'   )

    def test01_name_to_gen_2008(self):
        c = __class__._test_name_to_gen
        c('vs2008'      , 'Visual Studio 9 2008' + _sfx  )
        c('vs2008_32'   , 'Visual Studio 9 2008'         )
        c('vs2008_64'   , 'Visual Studio 9 2008 Win64'   )
        c('vs2008_ia64' , 'Visual Studio 9 2008 IA64'    )
        c('Visual Studio 9 2008' + _sfx  , 'Visual Studio 9 2008' + _sfx  )
        c('Visual Studio 9 2008'         , 'Visual Studio 9 2008'         )
        c('Visual Studio 9 2008 Win64'   , 'Visual Studio 9 2008 Win64'   )
        c('Visual Studio 9 2008 IA64'    , 'Visual Studio 9 2008 IA64'    )

    def test01_name_to_gen_2005(self):
        c = __class__._test_name_to_gen
        c('vs2005'      , 'Visual Studio 8 2005' + _sfx  )
        c('vs2005_32'   , 'Visual Studio 8 2005'         )
        c('vs2005_64'   , 'Visual Studio 8 2005 Win64'   )
        c('Visual Studio 8 2005' + _sfx  , 'Visual Studio 8 2005' + _sfx  )
        c('Visual Studio 8 2005'         , 'Visual Studio 8 2005'         )
        c('Visual Studio 8 2005 Win64'   , 'Visual Studio 8 2005 Win64'   )

    @staticmethod
    def _test_gen_to_name(a, s):
        sc = vsinfo.to_name(a)
        if sc != s:
            self.fail("{} should be '{}' but is '{}'".format(a, s, sc))

    def test02_gen_to_name_2022(self):
        c = __class__._test_gen_to_name
        c('Visual Studio 17 2022'        , 'vs2022_32'   )
        c('Visual Studio 17 2022 Win64'  , 'vs2022_64'   )
        c('Visual Studio 17 2022 ARM'    , 'vs2022_arm'  )
        c('Visual Studio 17 2022 ARM32'  , 'vs2022_arm32')
        c('Visual Studio 17 2022 ARM64'  , 'vs2022_arm64')
        c('vs2022'      , 'vs2022'      )
        c('vs2022_32'   , 'vs2022_32'   )
        c('vs2022_64'   , 'vs2022_64'   )
        c('vs2022_arm'  , 'vs2022_arm'  )
        c('vs2022_arm32', 'vs2022_arm32')
        c('vs2022_arm64', 'vs2022_arm64')

    def test02_gen_to_name_2019(self):
        c = __class__._test_gen_to_name
        c('Visual Studio 16 2019'        , 'vs2019_32'   )
        c('Visual Studio 16 2019 Win64'  , 'vs2019_64'   )
        c('Visual Studio 16 2019 ARM'    , 'vs2019_arm'  )
        c('Visual Studio 16 2019 ARM32'  , 'vs2019_arm32')
        c('Visual Studio 16 2019 ARM64'  , 'vs2019_arm64')
        c('vs2019'      , 'vs2019'      )
        c('vs2019_32'   , 'vs2019_32'   )
        c('vs2019_64'   , 'vs2019_64'   )
        c('vs2019_arm'  , 'vs2019_arm'  )
        c('vs2019_arm32', 'vs2019_arm32')
        c('vs2019_arm64', 'vs2019_arm64')

    def test02_gen_to_name_2017(self):
        c = __class__._test_gen_to_name
        c('Visual Studio 15 2017'        , 'vs2017_32'   )
        c('Visual Studio 15 2017 Win64'  , 'vs2017_64'   )
        c('Visual Studio 15 2017 ARM'    , 'vs2017_arm'  )
        c('vs2017'      , 'vs2017'      )
        c('vs2017_32'   , 'vs2017_32'   )
        c('vs2017_64'   , 'vs2017_64'   )
        c('vs2017_arm'  , 'vs2017_arm'  )

    def test02_gen_to_name_2015(self):
        c = __class__._test_gen_to_name
        c('Visual Studio 14 2015'        , 'vs2015_32'   )
        c('Visual Studio 14 2015 Win64'  , 'vs2015_64'   )
        c('Visual Studio 14 2015 ARM'    , 'vs2015_arm'  )
        c('vs2015'      , 'vs2015'      )
        c('vs2015_32'   , 'vs2015_32'   )
        c('vs2015_64'   , 'vs2015_64'   )
        c('vs2015_arm'  , 'vs2015_arm'  )

    def test02_gen_to_name_2013(self):
        c = __class__._test_gen_to_name
        c('Visual Studio 12 2013'        , 'vs2013_32'   )
        c('Visual Studio 12 2013 Win64'  , 'vs2013_64'   )
        c('Visual Studio 12 2013 ARM'    , 'vs2013_arm'  )
        c('vs2013'      , 'vs2013'      )
        c('vs2013_32'   , 'vs2013_32'   )
        c('vs2013_64'   , 'vs2013_64'   )
        c('vs2013_arm'  , 'vs2013_arm'  )

    def test02_gen_to_name_2012(self):
        c = __class__._test_gen_to_name
        c('Visual Studio 11 2012'        , 'vs2012_32'   )
        c('Visual Studio 11 2012 Win64'  , 'vs2012_64'   )
        c('Visual Studio 11 2012 ARM'    , 'vs2012_arm'  )
        c('vs2012'      , 'vs2012'      )
        c('vs2012_32'   , 'vs2012_32'   )
        c('vs2012_64'   , 'vs2012_64'   )
        c('vs2012_arm'  , 'vs2012_arm'  )

    def test02_gen_to_name_2010(self):
        c = __class__._test_gen_to_name
        c('Visual Studio 10 2010'        , 'vs2010_32'   )
        c('Visual Studio 10 2010 Win64'  , 'vs2010_64'   )
        c('Visual Studio 10 2010 IA64'   , 'vs2010_ia64' )
        c('vs2010'      , 'vs2010'      )
        c('vs2010_32'   , 'vs2010_32'   )
        c('vs2010_64'   , 'vs2010_64'   )
        c('vs2010_ia64' , 'vs2010_ia64' )

    def test02_gen_to_name_2008(self):
        c = __class__._test_gen_to_name
        c('Visual Studio 9 2008'         , 'vs2008_32'   )
        c('Visual Studio 9 2008 Win64'   , 'vs2008_64'   )
        c('Visual Studio 9 2008 IA64'    , 'vs2008_ia64' )
        c('vs2008'      , 'vs2008'      )
        c('vs2008_32'   , 'vs2008_32'   )
        c('vs2008_64'   , 'vs2008_64'   )
        c('vs2008_ia64' , 'vs2008_ia64' )

    def test02_gen_to_name_2005(self):
        c = __class__._test_gen_to_name
        c('Visual Studio 8 2005'         , 'vs2005_32'   )
        c('Visual Studio 8 2005 Win64'   , 'vs2005_64'   )
        c('vs2005'      , 'vs2005'      )
        c('vs2005_32'   , 'vs2005_32'   )
        c('vs2005_64'   , 'vs2005_64'   )

    @staticmethod
    def _test_parse_toolset(spec, name_vs, ts_vs):
        cname_vs, cts_vs = vsinfo.sep_name_toolset(spec)
        if cname_vs != name_vs:
            self.fail("{} should be '{}' but is '{}'".format(spec, name_vs, cname_vs))
        if cts_vs != ts_vs:
            self.fail("{} should be '{}' but is '{}'".format(spec, ts_vs, cts_vs))

    def test03_parse_toolset_2022(self):
        t = __class__._test_parse_toolset
        t('vs2022'                , 'vs2022'     , None           )
        t('vs2022_clang'          , 'vs2022'     , 'v143_clang_c2')
        t('vs2022_xp'             , 'vs2022'     , 'v143_xp'      )
        t('vs2022_v143'           , 'vs2022'     , 'v143'         )
        t('vs2022_v143_xp'        , 'vs2022'     , 'v143_xp'      )
        t('vs2022_v143_clang'     , 'vs2022'     , 'v143_clang_c2')
        t('vs2022_v142'           , 'vs2022'     , 'v142'         )
        t('vs2022_v142_xp'        , 'vs2022'     , 'v142_xp'      )
        t('vs2022_v142_clang'     , 'vs2022'     , 'v142_clang_c2')
        t('vs2022_v141'           , 'vs2022'     , 'v141'         )
        t('vs2022_v141_xp'        , 'vs2022'     , 'v141_xp'      )
        t('vs2022_v141_clang'     , 'vs2022'     , 'v141_clang_c2')
        t('vs2022_v140'           , 'vs2022'     , 'v140'         )
        t('vs2022_v140_xp'        , 'vs2022'     , 'v140_xp'      )
        t('vs2022_v140_clang'     , 'vs2022'     , 'v140_clang_c2')
        t('vs2022_v120'           , 'vs2022'     , 'v120'         )
        t('vs2022_v120_xp'        , 'vs2022'     , 'v120_xp'      )
        t('vs2022_v110'           , 'vs2022'     , 'v110'         )
        t('vs2022_v110_xp'        , 'vs2022'     , 'v110_xp'      )
        t('vs2022_v100'           , 'vs2022'     , 'v100'         )
        t('vs2022_v100_xp'        , 'vs2022'     , 'v100_xp'      )
        t('vs2022_v90'            , 'vs2022'     , 'v90'          )
        t('vs2022_v90_xp'         , 'vs2022'     , 'v90_xp'       )
        t('vs2022_v80'            , 'vs2022'     , 'v80'          )

        t('vs2022_32'             , 'vs2022_32'  , None           )
        t('vs2022_32_clang'       , 'vs2022_32'  , 'v143_clang_c2')
        t('vs2022_32_xp'          , 'vs2022_32'  , 'v143_xp'      )
        t('vs2022_32_v143'        , 'vs2022_32'  , 'v143'         )
        t('vs2022_32_v143_xp'     , 'vs2022_32'  , 'v143_xp'      )
        t('vs2022_32_v143_clang'  , 'vs2022_32'  , 'v143_clang_c2')
        t('vs2022_32_v142'        , 'vs2022_32'  , 'v142'         )
        t('vs2022_32_v142_xp'     , 'vs2022_32'  , 'v142_xp'      )
        t('vs2022_32_v142_clang'  , 'vs2022_32'  , 'v142_clang_c2')
        t('vs2022_32_v141'        , 'vs2022_32'  , 'v141'         )
        t('vs2022_32_v141_xp'     , 'vs2022_32'  , 'v141_xp'      )
        t('vs2022_32_v141_clang'  , 'vs2022_32'  , 'v141_clang_c2')
        t('vs2022_32_v140'        , 'vs2022_32'  , 'v140'         )
        t('vs2022_32_v140_xp'     , 'vs2022_32'  , 'v140_xp'      )
        t('vs2022_32_v140_clang'  , 'vs2022_32'  , 'v140_clang_c2')
        t('vs2022_32_v120'        , 'vs2022_32'  , 'v120'         )
        t('vs2022_32_v120_xp'     , 'vs2022_32'  , 'v120_xp'      )
        t('vs2022_32_v110'        , 'vs2022_32'  , 'v110'         )
        t('vs2022_32_v110_xp'     , 'vs2022_32'  , 'v110_xp'      )
        t('vs2022_32_v100'        , 'vs2022_32'  , 'v100'         )
        t('vs2022_32_v100_xp'     , 'vs2022_32'  , 'v100_xp'      )
        t('vs2022_32_v90'         , 'vs2022_32'  , 'v90'          )
        t('vs2022_32_v90_xp'      , 'vs2022_32'  , 'v90_xp'       )
        t('vs2022_32_v80'         , 'vs2022_32'  , 'v80'          )

        t('vs2022_64'             , 'vs2022_64'  , None           )
        t('vs2022_64_clang'       , 'vs2022_64'  , 'v143_clang_c2')
        t('vs2022_64_xp'          , 'vs2022_64'  , 'v143_xp'      )
        t('vs2022_64_v143'        , 'vs2022_64'  , 'v143'         )
        t('vs2022_64_v143_xp'     , 'vs2022_64'  , 'v143_xp'      )
        t('vs2022_64_v143_clang'  , 'vs2022_64'  , 'v143_clang_c2')
        t('vs2022_64_v142'        , 'vs2022_64'  , 'v142'         )
        t('vs2022_64_v142_xp'     , 'vs2022_64'  , 'v142_xp'      )
        t('vs2022_64_v142_clang'  , 'vs2022_64'  , 'v142_clang_c2')
        t('vs2022_64_v141'        , 'vs2022_64'  , 'v141'         )
        t('vs2022_64_v141_xp'     , 'vs2022_64'  , 'v141_xp'      )
        t('vs2022_64_v141_clang'  , 'vs2022_64'  , 'v141_clang_c2')
        t('vs2022_64_v140'        , 'vs2022_64'  , 'v140'         )
        t('vs2022_64_v140_xp'     , 'vs2022_64'  , 'v140_xp'      )
        t('vs2022_64_v140_clang'  , 'vs2022_64'  , 'v140_clang_c2')
        t('vs2022_64_v120'        , 'vs2022_64'  , 'v120'         )
        t('vs2022_64_v120_xp'     , 'vs2022_64'  , 'v120_xp'      )
        t('vs2022_64_v110'        , 'vs2022_64'  , 'v110'         )
        t('vs2022_64_v110_xp'     , 'vs2022_64'  , 'v110_xp'      )
        t('vs2022_64_v100'        , 'vs2022_64'  , 'v100'         )
        t('vs2022_64_v100_xp'     , 'vs2022_64'  , 'v100_xp'      )
        t('vs2022_64_v90'         , 'vs2022_64'  , 'v90'          )
        t('vs2022_64_v90_xp'      , 'vs2022_64'  , 'v90_xp'       )
        t('vs2022_64_v80'         , 'vs2022_64'  , 'v80'          )

        t('vs2022_arm'            , 'vs2022_arm' , None           )
        t('vs2022_arm_clang'      , 'vs2022_arm' , 'v143_clang_c2')
        t('vs2022_arm_v143'       , 'vs2022_arm' , 'v143'         )
        t('vs2022_arm_v143_clang' , 'vs2022_arm' , 'v143_clang_c2')
        t('vs2022_arm_v142'       , 'vs2022_arm' , 'v142'         )
        t('vs2022_arm_v142_clang' , 'vs2022_arm' , 'v142_clang_c2')
        t('vs2022_arm_v141'       , 'vs2022_arm' , 'v141'         )
        t('vs2022_arm_v141_clang' , 'vs2022_arm' , 'v141_clang_c2')
        t('vs2022_arm_v140'       , 'vs2022_arm' , 'v140'         )
        t('vs2022_arm_v140_clang' , 'vs2022_arm' , 'v140_clang_c2')
        t('vs2022_arm_v120'       , 'vs2022_arm' , 'v120'         )
        t('vs2022_arm_v110'       , 'vs2022_arm' , 'v110'         )
        t('vs2022_arm_v100'       , 'vs2022_arm' , 'v100'         )

        t('vs2022_arm32'            , 'vs2022_arm32' , None           )
        t('vs2022_arm32_clang'      , 'vs2022_arm32' , 'v143_clang_c2')
        t('vs2022_arm32_v143'       , 'vs2022_arm32' , 'v143'         )
        t('vs2022_arm32_v143_clang' , 'vs2022_arm32' , 'v143_clang_c2')
        t('vs2022_arm32_v142'       , 'vs2022_arm32' , 'v142'         )
        t('vs2022_arm32_v142_clang' , 'vs2022_arm32' , 'v142_clang_c2')
        t('vs2022_arm32_v141'       , 'vs2022_arm32' , 'v141'         )
        t('vs2022_arm32_v141_clang' , 'vs2022_arm32' , 'v141_clang_c2')
        t('vs2022_arm32_v140'       , 'vs2022_arm32' , 'v140'         )
        t('vs2022_arm32_v140_clang' , 'vs2022_arm32' , 'v140_clang_c2')
        t('vs2022_arm32_v120'       , 'vs2022_arm32' , 'v120'         )
        t('vs2022_arm32_v110'       , 'vs2022_arm32' , 'v110'         )
        t('vs2022_arm32_v100'       , 'vs2022_arm32' , 'v100'         )

        t('vs2022_arm64'            , 'vs2022_arm64' , None           )
        t('vs2022_arm64_clang'      , 'vs2022_arm64' , 'v143_clang_c2')
        t('vs2022_arm64_v143'       , 'vs2022_arm64' , 'v143'         )
        t('vs2022_arm64_v143_clang' , 'vs2022_arm64' , 'v143_clang_c2')
        t('vs2022_arm64_v142'       , 'vs2022_arm64' , 'v142'         )
        t('vs2022_arm64_v142_clang' , 'vs2022_arm64' , 'v142_clang_c2')
        t('vs2022_arm64_v141'       , 'vs2022_arm64' , 'v141'         )
        t('vs2022_arm64_v141_clang' , 'vs2022_arm64' , 'v141_clang_c2')
        t('vs2022_arm64_v140'       , 'vs2022_arm64' , 'v140'         )
        t('vs2022_arm64_v140_clang' , 'vs2022_arm64' , 'v140_clang_c2')
        t('vs2022_arm64_v120'       , 'vs2022_arm64' , 'v120'         )
        t('vs2022_arm64_v110'       , 'vs2022_arm64' , 'v110'         )
        t('vs2022_arm64_v100'       , 'vs2022_arm64' , 'v100'         )

    def test03_parse_toolset_2019(self):
        t = __class__._test_parse_toolset
        t('vs2019'                , 'vs2019'     , None           )
        t('vs2019_clang'          , 'vs2019'     , 'v142_clang_c2')
        t('vs2019_xp'             , 'vs2019'     , 'v142_xp'      )
        t('vs2019_v142'           , 'vs2019'     , 'v142'         )
        t('vs2019_v142_xp'        , 'vs2019'     , 'v142_xp'      )
        t('vs2019_v142_clang'     , 'vs2019'     , 'v142_clang_c2')
        t('vs2019_v141'           , 'vs2019'     , 'v141'         )
        t('vs2019_v141_xp'        , 'vs2019'     , 'v141_xp'      )
        t('vs2019_v141_clang'     , 'vs2019'     , 'v141_clang_c2')
        t('vs2019_v140'           , 'vs2019'     , 'v140'         )
        t('vs2019_v140_xp'        , 'vs2019'     , 'v140_xp'      )
        t('vs2019_v140_clang'     , 'vs2019'     , 'v140_clang_c2')
        t('vs2019_v120'           , 'vs2019'     , 'v120'         )
        t('vs2019_v120_xp'        , 'vs2019'     , 'v120_xp'      )
        t('vs2019_v110'           , 'vs2019'     , 'v110'         )
        t('vs2019_v110_xp'        , 'vs2019'     , 'v110_xp'      )
        t('vs2019_v100'           , 'vs2019'     , 'v100'         )
        t('vs2019_v100_xp'        , 'vs2019'     , 'v100_xp'      )
        t('vs2019_v90'            , 'vs2019'     , 'v90'          )
        t('vs2019_v90_xp'         , 'vs2019'     , 'v90_xp'       )
        t('vs2019_v80'            , 'vs2019'     , 'v80'          )

        t('vs2019_32'             , 'vs2019_32'  , None           )
        t('vs2019_32_clang'       , 'vs2019_32'  , 'v142_clang_c2')
        t('vs2019_32_xp'          , 'vs2019_32'  , 'v142_xp'      )
        t('vs2019_32_v142'        , 'vs2019_32'  , 'v142'         )
        t('vs2019_32_v142_xp'     , 'vs2019_32'  , 'v142_xp'      )
        t('vs2019_32_v142_clang'  , 'vs2019_32'  , 'v142_clang_c2')
        t('vs2019_32_v141'        , 'vs2019_32'  , 'v141'         )
        t('vs2019_32_v141_xp'     , 'vs2019_32'  , 'v141_xp'      )
        t('vs2019_32_v141_clang'  , 'vs2019_32'  , 'v141_clang_c2')
        t('vs2019_32_v140'        , 'vs2019_32'  , 'v140'         )
        t('vs2019_32_v140_xp'     , 'vs2019_32'  , 'v140_xp'      )
        t('vs2019_32_v140_clang'  , 'vs2019_32'  , 'v140_clang_c2')
        t('vs2019_32_v120'        , 'vs2019_32'  , 'v120'         )
        t('vs2019_32_v120_xp'     , 'vs2019_32'  , 'v120_xp'      )
        t('vs2019_32_v110'        , 'vs2019_32'  , 'v110'         )
        t('vs2019_32_v110_xp'     , 'vs2019_32'  , 'v110_xp'      )
        t('vs2019_32_v100'        , 'vs2019_32'  , 'v100'         )
        t('vs2019_32_v100_xp'     , 'vs2019_32'  , 'v100_xp'      )
        t('vs2019_32_v90'         , 'vs2019_32'  , 'v90'          )
        t('vs2019_32_v90_xp'      , 'vs2019_32'  , 'v90_xp'       )
        t('vs2019_32_v80'         , 'vs2019_32'  , 'v80'          )

        t('vs2019_64'             , 'vs2019_64'  , None           )
        t('vs2019_64_clang'       , 'vs2019_64'  , 'v142_clang_c2')
        t('vs2019_64_xp'          , 'vs2019_64'  , 'v142_xp'      )
        t('vs2019_64_v142'        , 'vs2019_64'  , 'v142'         )
        t('vs2019_64_v142_xp'     , 'vs2019_64'  , 'v142_xp'      )
        t('vs2019_64_v142_clang'  , 'vs2019_64'  , 'v142_clang_c2')
        t('vs2019_64_v141'        , 'vs2019_64'  , 'v141'         )
        t('vs2019_64_v141_xp'     , 'vs2019_64'  , 'v141_xp'      )
        t('vs2019_64_v141_clang'  , 'vs2019_64'  , 'v141_clang_c2')
        t('vs2019_64_v140'        , 'vs2019_64'  , 'v140'         )
        t('vs2019_64_v140_xp'     , 'vs2019_64'  , 'v140_xp'      )
        t('vs2019_64_v140_clang'  , 'vs2019_64'  , 'v140_clang_c2')
        t('vs2019_64_v120'        , 'vs2019_64'  , 'v120'         )
        t('vs2019_64_v120_xp'     , 'vs2019_64'  , 'v120_xp'      )
        t('vs2019_64_v110'        , 'vs2019_64'  , 'v110'         )
        t('vs2019_64_v110_xp'     , 'vs2019_64'  , 'v110_xp'      )
        t('vs2019_64_v100'        , 'vs2019_64'  , 'v100'         )
        t('vs2019_64_v100_xp'     , 'vs2019_64'  , 'v100_xp'      )
        t('vs2019_64_v90'         , 'vs2019_64'  , 'v90'          )
        t('vs2019_64_v90_xp'      , 'vs2019_64'  , 'v90_xp'       )
        t('vs2019_64_v80'         , 'vs2019_64'  , 'v80'          )

        t('vs2019_arm'            , 'vs2019_arm' , None           )
        t('vs2019_arm_clang'      , 'vs2019_arm' , 'v142_clang_c2')
        t('vs2019_arm_v142'       , 'vs2019_arm' , 'v142'         )
        t('vs2019_arm_v142_clang' , 'vs2019_arm' , 'v142_clang_c2')
        t('vs2019_arm_v141'       , 'vs2019_arm' , 'v141'         )
        t('vs2019_arm_v141_clang' , 'vs2019_arm' , 'v141_clang_c2')
        t('vs2019_arm_v140'       , 'vs2019_arm' , 'v140'         )
        t('vs2019_arm_v140_clang' , 'vs2019_arm' , 'v140_clang_c2')
        t('vs2019_arm_v120'       , 'vs2019_arm' , 'v120'         )
        t('vs2019_arm_v110'       , 'vs2019_arm' , 'v110'         )
        t('vs2019_arm_v100'       , 'vs2019_arm' , 'v100'         )

        t('vs2019_arm32'            , 'vs2019_arm32' , None           )
        t('vs2019_arm32_clang'      , 'vs2019_arm32' , 'v142_clang_c2')
        t('vs2019_arm32_v142'       , 'vs2019_arm32' , 'v142'         )
        t('vs2019_arm32_v142_clang' , 'vs2019_arm32' , 'v142_clang_c2')
        t('vs2019_arm32_v141'       , 'vs2019_arm32' , 'v141'         )
        t('vs2019_arm32_v141_clang' , 'vs2019_arm32' , 'v141_clang_c2')
        t('vs2019_arm32_v140'       , 'vs2019_arm32' , 'v140'         )
        t('vs2019_arm32_v140_clang' , 'vs2019_arm32' , 'v140_clang_c2')
        t('vs2019_arm32_v120'       , 'vs2019_arm32' , 'v120'         )
        t('vs2019_arm32_v110'       , 'vs2019_arm32' , 'v110'         )
        t('vs2019_arm32_v100'       , 'vs2019_arm32' , 'v100'         )

        t('vs2019_arm64'            , 'vs2019_arm64' , None           )
        t('vs2019_arm64_clang'      , 'vs2019_arm64' , 'v142_clang_c2')
        t('vs2019_arm64_v142'       , 'vs2019_arm64' , 'v142'         )
        t('vs2019_arm64_v142_clang' , 'vs2019_arm64' , 'v142_clang_c2')
        t('vs2019_arm64_v141'       , 'vs2019_arm64' , 'v141'         )
        t('vs2019_arm64_v141_clang' , 'vs2019_arm64' , 'v141_clang_c2')
        t('vs2019_arm64_v140'       , 'vs2019_arm64' , 'v140'         )
        t('vs2019_arm64_v140_clang' , 'vs2019_arm64' , 'v140_clang_c2')
        t('vs2019_arm64_v120'       , 'vs2019_arm64' , 'v120'         )
        t('vs2019_arm64_v110'       , 'vs2019_arm64' , 'v110'         )
        t('vs2019_arm64_v100'       , 'vs2019_arm64' , 'v100'         )

    def test03_parse_toolset_2017(self):
        t = __class__._test_parse_toolset
        t('vs2017'                , 'vs2017'     , None           )
        t('vs2017_clang'          , 'vs2017'     , 'v141_clang_c2')
        t('vs2017_xp'             , 'vs2017'     , 'v141_xp'      )
        t('vs2017_v141'           , 'vs2017'     , 'v141'         )
        t('vs2017_v141_xp'        , 'vs2017'     , 'v141_xp'      )
        t('vs2017_v141_clang'     , 'vs2017'     , 'v141_clang_c2')
        t('vs2017_v140'           , 'vs2017'     , 'v140'         )
        t('vs2017_v140_xp'        , 'vs2017'     , 'v140_xp'      )
        t('vs2017_v140_clang'     , 'vs2017'     , 'v140_clang_c2')
        t('vs2017_v120'           , 'vs2017'     , 'v120'         )
        t('vs2017_v120_xp'        , 'vs2017'     , 'v120_xp'      )
        t('vs2017_v110'           , 'vs2017'     , 'v110'         )
        t('vs2017_v110_xp'        , 'vs2017'     , 'v110_xp'      )
        t('vs2017_v100'           , 'vs2017'     , 'v100'         )
        t('vs2017_v100_xp'        , 'vs2017'     , 'v100_xp'      )
        t('vs2017_v90'            , 'vs2017'     , 'v90'          )
        t('vs2017_v90_xp'         , 'vs2017'     , 'v90_xp'       )
        t('vs2017_v80'            , 'vs2017'     , 'v80'          )

        t('vs2017_32'             , 'vs2017_32'  , None           )
        t('vs2017_32_clang'       , 'vs2017_32'  , 'v141_clang_c2')
        t('vs2017_32_xp'          , 'vs2017_32'  , 'v141_xp'      )
        t('vs2017_32_v141'        , 'vs2017_32'  , 'v141'         )
        t('vs2017_32_v141_xp'     , 'vs2017_32'  , 'v141_xp'      )
        t('vs2017_32_v141_clang'  , 'vs2017_32'  , 'v141_clang_c2')
        t('vs2017_32_v140'        , 'vs2017_32'  , 'v140'         )
        t('vs2017_32_v140_xp'     , 'vs2017_32'  , 'v140_xp'      )
        t('vs2017_32_v140_clang'  , 'vs2017_32'  , 'v140_clang_c2')
        t('vs2017_32_v120'        , 'vs2017_32'  , 'v120'         )
        t('vs2017_32_v120_xp'     , 'vs2017_32'  , 'v120_xp'      )
        t('vs2017_32_v110'        , 'vs2017_32'  , 'v110'         )
        t('vs2017_32_v110_xp'     , 'vs2017_32'  , 'v110_xp'      )
        t('vs2017_32_v100'        , 'vs2017_32'  , 'v100'         )
        t('vs2017_32_v100_xp'     , 'vs2017_32'  , 'v100_xp'      )
        t('vs2017_32_v90'         , 'vs2017_32'  , 'v90'          )
        t('vs2017_32_v90_xp'      , 'vs2017_32'  , 'v90_xp'       )
        t('vs2017_32_v80'         , 'vs2017_32'  , 'v80'          )

        t('vs2017_64'             , 'vs2017_64'  , None           )
        t('vs2017_64_clang'       , 'vs2017_64'  , 'v141_clang_c2')
        t('vs2017_64_xp'          , 'vs2017_64'  , 'v141_xp'      )
        t('vs2017_64_v141'        , 'vs2017_64'  , 'v141'         )
        t('vs2017_64_v141_xp'     , 'vs2017_64'  , 'v141_xp'      )
        t('vs2017_64_v141_clang'  , 'vs2017_64'  , 'v141_clang_c2')
        t('vs2017_64_v140'        , 'vs2017_64'  , 'v140'         )
        t('vs2017_64_v140_xp'     , 'vs2017_64'  , 'v140_xp'      )
        t('vs2017_64_v140_clang'  , 'vs2017_64'  , 'v140_clang_c2')
        t('vs2017_64_v120'        , 'vs2017_64'  , 'v120'         )
        t('vs2017_64_v120_xp'     , 'vs2017_64'  , 'v120_xp'      )
        t('vs2017_64_v110'        , 'vs2017_64'  , 'v110'         )
        t('vs2017_64_v110_xp'     , 'vs2017_64'  , 'v110_xp'      )
        t('vs2017_64_v100'        , 'vs2017_64'  , 'v100'         )
        t('vs2017_64_v100_xp'     , 'vs2017_64'  , 'v100_xp'      )
        t('vs2017_64_v90'         , 'vs2017_64'  , 'v90'          )
        t('vs2017_64_v90_xp'      , 'vs2017_64'  , 'v90_xp'       )
        t('vs2017_64_v80'         , 'vs2017_64'  , 'v80'          )

        t('vs2017_arm'            , 'vs2017_arm' , None           )
        t('vs2017_arm_clang'      , 'vs2017_arm' , 'v141_clang_c2')
        t('vs2017_arm_v141'       , 'vs2017_arm' , 'v141'         )
        t('vs2017_arm_v141_clang' , 'vs2017_arm' , 'v141_clang_c2')
        t('vs2017_arm_v140'       , 'vs2017_arm' , 'v140'         )
        t('vs2017_arm_v140_clang' , 'vs2017_arm' , 'v140_clang_c2')
        t('vs2017_arm_v120'       , 'vs2017_arm' , 'v120'         )
        t('vs2017_arm_v110'       , 'vs2017_arm' , 'v110'         )
        t('vs2017_arm_v100'       , 'vs2017_arm' , 'v100'         )

    def test03_parse_toolset_2015(self):
        t = __class__._test_parse_toolset
        t('vs2015'                , 'vs2015'     , None           )
        t('vs2015_clang'          , 'vs2015'     , 'v140_clang_c2')
        t('vs2015_xp'             , 'vs2015'     , 'v140_xp'      )
        t('vs2015_v140'           , 'vs2015'     , 'v140'         )
        t('vs2015_v140_xp'        , 'vs2015'     , 'v140_xp'      )
        t('vs2015_v140_clang'     , 'vs2015'     , 'v140_clang_c2')
        t('vs2015_v120'           , 'vs2015'     , 'v120'         )
        t('vs2015_v120_xp'        , 'vs2015'     , 'v120_xp'      )
        t('vs2015_v110'           , 'vs2015'     , 'v110'         )
        t('vs2015_v110_xp'        , 'vs2015'     , 'v110_xp'      )
        t('vs2015_v100'           , 'vs2015'     , 'v100'         )
        t('vs2015_v100_xp'        , 'vs2015'     , 'v100_xp'      )
        t('vs2015_v90'            , 'vs2015'     , 'v90'          )
        t('vs2015_v90_xp'         , 'vs2015'     , 'v90_xp'       )
        t('vs2015_v80'            , 'vs2015'     , 'v80'          )

        t('vs2015_32'             , 'vs2015_32'  , None           )
        t('vs2015_32_clang'       , 'vs2015_32'  , 'v140_clang_c2')
        t('vs2015_32_xp'          , 'vs2015_32'  , 'v140_xp'      )
        t('vs2015_32_v140'        , 'vs2015_32'  , 'v140'         )
        t('vs2015_32_v140_xp'     , 'vs2015_32'  , 'v140_xp'      )
        t('vs2015_32_v140_clang'  , 'vs2015_32'  , 'v140_clang_c2')
        t('vs2015_32_v120'        , 'vs2015_32'  , 'v120'         )
        t('vs2015_32_v120_xp'     , 'vs2015_32'  , 'v120_xp'      )
        t('vs2015_32_v110'        , 'vs2015_32'  , 'v110'         )
        t('vs2015_32_v110_xp'     , 'vs2015_32'  , 'v110_xp'      )
        t('vs2015_32_v100'        , 'vs2015_32'  , 'v100'         )
        t('vs2015_32_v100_xp'     , 'vs2015_32'  , 'v100_xp'      )

        t('vs2015_64'             , 'vs2015_64'  , None           )
        t('vs2015_64_clang'       , 'vs2015_64'  , 'v140_clang_c2')
        t('vs2015_64_xp'          , 'vs2015_64'  , 'v140_xp'      )
        t('vs2015_64_v140'        , 'vs2015_64'  , 'v140'         )
        t('vs2015_64_v140_xp'     , 'vs2015_64'  , 'v140_xp'      )
        t('vs2015_64_v140_clang'  , 'vs2015_64'  , 'v140_clang_c2')
        t('vs2015_64_v120'        , 'vs2015_64'  , 'v120'         )
        t('vs2015_64_v120_xp'     , 'vs2015_64'  , 'v120_xp'      )
        t('vs2015_64_v110'        , 'vs2015_64'  , 'v110'         )
        t('vs2015_64_v110_xp'     , 'vs2015_64'  , 'v110_xp'      )
        t('vs2015_64_v100'        , 'vs2015_64'  , 'v100'         )
        t('vs2015_64_v100_xp'     , 'vs2015_64'  , 'v100_xp'      )
        t('vs2015_arm'            , 'vs2015_arm' , None           )
        t('vs2015_arm_clang'      , 'vs2015_arm' , 'v140_clang_c2')

    def test03_parse_toolset_2013(self):
        t = __class__._test_parse_toolset
        t('vs2013'                , 'vs2013'    , None           )
        t('vs2013_xp'             , 'vs2013'    , 'v120_xp'      )
        t('vs2013_v110'           , 'vs2013'    , 'v110'         )
        t('vs2013_v110_xp'        , 'vs2013'    , 'v110_xp'      )
        t('vs2013_v100'           , 'vs2013'    , 'v100'         )
        t('vs2013_v100_xp'        , 'vs2013'    , 'v100_xp'      )
        t('vs2013_v90'            , 'vs2013'    , 'v90'          )
        t('vs2013_v90_xp'         , 'vs2013'    , 'v90_xp'       )
        t('vs2013_v80'            , 'vs2013'    , 'v80'          )

        t('vs2013_32'             , 'vs2013_32' , None           )
        t('vs2013_32_xp'          , 'vs2013_32' , 'v120_xp'      )
        t('vs2013_32_v110'        , 'vs2013_32' , 'v110'         )
        t('vs2013_32_v110_xp'     , 'vs2013_32' , 'v110_xp'      )
        t('vs2013_32_v100'        , 'vs2013_32' , 'v100'         )
        t('vs2013_32_v100_xp'     , 'vs2013_32' , 'v100_xp'      )
        t('vs2013_32_v90'         , 'vs2013_32' , 'v90'          )
        t('vs2013_32_v90_xp'      , 'vs2013_32' , 'v90_xp'       )
        t('vs2013_32_v80'         , 'vs2013_32' , 'v80'          )

        t('vs2013_64'             , 'vs2013_64' , None           )
        t('vs2013_64_xp'          , 'vs2013_64' , 'v120_xp'      )
        t('vs2013_64_v110'        , 'vs2013_64' , 'v110'         )
        t('vs2013_64_v110_xp'     , 'vs2013_64' , 'v110_xp'      )
        t('vs2013_64_v100'        , 'vs2013_64' , 'v100'         )
        t('vs2013_64_v100_xp'     , 'vs2013_64' , 'v100_xp'      )
        t('vs2013_64_v90'         , 'vs2013_64' , 'v90'          )
        t('vs2013_64_v90_xp'      , 'vs2013_64' , 'v90_xp'       )
        t('vs2013_64_v80'         , 'vs2013_64' , 'v80'          )

    def test03_parse_toolset_2012(self):
        t = __class__._test_parse_toolset
        t('vs2012'                , 'vs2012'    , None           )
        t('vs2012_xp'             , 'vs2012'    , 'v110_xp'      )
        t('vs2012_v110'           , 'vs2012'    , 'v110'         )
        t('vs2012_v110_xp'        , 'vs2012'    , 'v110_xp'      )
        t('vs2012_v100'           , 'vs2012'    , 'v100'         )
        t('vs2012_v100_xp'        , 'vs2012'    , 'v100_xp'      )
        t('vs2012_v90'            , 'vs2012'    , 'v90'          )
        t('vs2012_v90_xp'         , 'vs2012'    , 'v90_xp'       )
        t('vs2012_v80'            , 'vs2012'    , 'v80'          )

        t('vs2012_32'             , 'vs2012_32' , None           )
        t('vs2012_32_xp'          , 'vs2012_32' , 'v110_xp'      )
        t('vs2012_32_v110'        , 'vs2012_32' , 'v110'         )
        t('vs2012_32_v110_xp'     , 'vs2012_32' , 'v110_xp'      )
        t('vs2012_32_v100'        , 'vs2012_32' , 'v100'         )
        t('vs2012_32_v100_xp'     , 'vs2012_32' , 'v100_xp'      )
        t('vs2012_32_v90'         , 'vs2012_32' , 'v90'          )
        t('vs2012_32_v90_xp'      , 'vs2012_32' , 'v90_xp'       )
        t('vs2012_32_v80'         , 'vs2012_32' , 'v80'          )

        t('vs2012_64'             , 'vs2012_64' , None           )
        t('vs2012_64_xp'          , 'vs2012_64' , 'v110_xp'      )
        t('vs2012_64_v110'        , 'vs2012_64' , 'v110'         )
        t('vs2012_64_v110_xp'     , 'vs2012_64' , 'v110_xp'      )
        t('vs2012_64_v100'        , 'vs2012_64' , 'v100'         )
        t('vs2012_64_v100_xp'     , 'vs2012_64' , 'v100_xp'      )
        t('vs2012_64_v90'         , 'vs2012_64' , 'v90'          )
        t('vs2012_64_v90_xp'      , 'vs2012_64' , 'v90_xp'       )
        t('vs2012_64_v80'         , 'vs2012_64' , 'v80'          )

    def test03_parse_toolset_2010(self):
        t = __class__._test_parse_toolset
        t('vs2010'                , 'vs2010'    , None           )
        t('vs2010_xp'             , 'vs2010'    , 'v100_xp'      )
        t('vs2010_v100'           , 'vs2010'    , 'v100'         )
        t('vs2010_v100_xp'        , 'vs2010'    , 'v100_xp'      )
        t('vs2010_v90'            , 'vs2010'    , 'v90'          )
        t('vs2010_v90_xp'         , 'vs2010'    , 'v90_xp'       )
        t('vs2010_v80'            , 'vs2010'    , 'v80'          )

        t('vs2010_32'             , 'vs2010_32' , None           )
        t('vs2010_32_xp'          , 'vs2010_32' , 'v100_xp'      )
        t('vs2010_32_v100'        , 'vs2010_32' , 'v100'         )
        t('vs2010_32_v100_xp'     , 'vs2010_32' , 'v100_xp'      )
        t('vs2010_32_v90'         , 'vs2010_32' , 'v90'          )
        t('vs2010_32_v90_xp'      , 'vs2010_32' , 'v90_xp'       )
        t('vs2010_32_v80'         , 'vs2010_32' , 'v80'          )

        t('vs2010_64'             , 'vs2010_64' , None           )
        t('vs2010_64_xp'          , 'vs2010_64' , 'v100_xp'      )
        t('vs2010_64_v100'        , 'vs2010_64' , 'v100'         )
        t('vs2010_64_v100_xp'     , 'vs2010_64' , 'v100_xp'      )
        t('vs2010_64_v90'         , 'vs2010_64' , 'v90'          )
        t('vs2010_64_v90_xp'      , 'vs2010_64' , 'v90_xp'       )
        t('vs2010_64_v80'         , 'vs2010_64' , 'v80'          )

        t('vs2010_ia64'           , 'vs2010_ia64' , None         )
        t('vs2010_ia64_xp'        , 'vs2010_ia64' , 'v100_xp'    )
        t('vs2010_ia64_v100'      , 'vs2010_ia64' , 'v100'       )
        t('vs2010_ia64_v100_xp'   , 'vs2010_ia64' , 'v100_xp'    )
        t('vs2010_ia64_v90'       , 'vs2010_ia64' , 'v90'        )
        t('vs2010_ia64_v90_xp'    , 'vs2010_ia64' , 'v90_xp'     )
        t('vs2010_ia64_v80'       , 'vs2010_ia64' , 'v80'        )

    def test03_parse_toolset_2008(self):
        t = __class__._test_parse_toolset
        t('vs2008'                , 'vs2008'    , None           )
        t('vs2008_xp'             , 'vs2008'    , 'v90_xp'       )
        t('vs2008_v90'            , 'vs2008'    , 'v90'          )
        t('vs2008_v90_xp'         , 'vs2008'    , 'v90_xp'       )
        t('vs2008_v80'            , 'vs2008'    , 'v80'          )

        t('vs2008_32'             , 'vs2008_32' , None           )
        t('vs2008_32_xp'          , 'vs2008_32' , 'v90_xp'       )
        t('vs2008_32_v90'         , 'vs2008_32' , 'v90'          )
        t('vs2008_32_v90_xp'      , 'vs2008_32' , 'v90_xp'       )
        t('vs2008_32_v80'         , 'vs2008_32' , 'v80'          )

        t('vs2008_64'             , 'vs2008_64' , None           )
        t('vs2008_64_xp'          , 'vs2008_64' , 'v90_xp'       )
        t('vs2008_64_v90'         , 'vs2008_64' , 'v90'          )
        t('vs2008_64_v90_xp'      , 'vs2008_64' , 'v90_xp'       )
        t('vs2008_64_v80'         , 'vs2008_64' , 'v80'          )

        t('vs2008_ia64'           , 'vs2008_ia64' , None         )
        t('vs2008_ia64_xp'        , 'vs2008_ia64' , 'v90_xp'     )
        t('vs2008_ia64_v90'       , 'vs2008_ia64' , 'v90'        )
        t('vs2008_ia64_v90_xp'    , 'vs2008_ia64' , 'v90_xp'     )
        t('vs2008_ia64_v80'       , 'vs2008_ia64' , 'v80'        )

    def test03_parse_toolset_2005(self):
        t = __class__._test_parse_toolset
        t('vs2005'                , 'vs2005'    , None           )
        t('vs2005_v80'            , 'vs2005'    , 'v80'          )

        t('vs2005_32'             , 'vs2005_32' , None           )
        t('vs2005_32_v80'         , 'vs2005_32' , 'v80'          )

        t('vs2005_64'             , 'vs2005_64' , None           )
        t('vs2005_64_v80'         , 'vs2005_64' , 'v80'          )


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    ut.main()
