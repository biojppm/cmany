#!/usr/bin/env python3

import unittest as ut
from c4.cmany import *
from c4.cmany.vsinfo import *
import os.path


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class TestSplitEsc(ut.TestCase):

    def test(self):
        from c4.cmany.util import splitesc
        self.assertEqual(splitesc('hello\,world,yet\,another', ','), ['hello\,world','yet\,another'])


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if System.default_str() == 'windows':

    class TestVisualStudioInfo(ut.TestCase):

        def test00_instances(self):
            for k in VisualStudioInfo.order:
                vs = VisualStudioInfo(k)
                self.assertIsInstance(vs.year, int)
                def c(w):
                    if not os.path.exists(w):
                        self.fail(vs.name + ": " + w + " does not exist")
                if vs.is_installed:
                    print("Found", vs.name, "aka", vs.gen + ":", vs.dir)
                    c(vs.dir)
                    c(vs.vcvarsall)
                    c(vs.msbuild)
                    c(vs.cxx_compiler)
                    c(vs.c_compiler)

        #def test01_find_any(self):
        #    any = VisualStudioInfo.find_any()
        #    if any is None:
        #        self.fail("could not find any VS installation")
        #    self.assertIsNotNone(any)

        def test01_name_to_gen(self):
            def c(a, s):
                sc = VisualStudioInfo.to_gen(a)
                if sc != s:
                    self.fail("{} should be '{}' but is '{}'".format(a, s, sc))
            _sfx = " Win64" if Architecture.default().is64 else ""
            c('vs2017'      , 'Visual Studio 15 2017' + _sfx )
            c('vs2017_32'   , 'Visual Studio 15 2017'        )
            c('vs2017_64'   , 'Visual Studio 15 2017 Win64'  )
            c('vs2017_arm'  , 'Visual Studio 15 2017 ARM'    )
            c('vs2015'      , 'Visual Studio 14 2015' + _sfx )
            c('vs2015_32'   , 'Visual Studio 14 2015'        )
            c('vs2015_64'   , 'Visual Studio 14 2015 Win64'  )
            c('vs2015_arm'  , 'Visual Studio 14 2015 ARM'    )
            c('vs2013'      , 'Visual Studio 12 2013' + _sfx )
            c('vs2013_32'   , 'Visual Studio 12 2013'        )
            c('vs2013_64'   , 'Visual Studio 12 2013 Win64'  )
            c('vs2013_arm'  , 'Visual Studio 12 2013 ARM'    )
            c('vs2012'      , 'Visual Studio 11 2012' + _sfx )
            c('vs2012_32'   , 'Visual Studio 11 2012'        )
            c('vs2012_64'   , 'Visual Studio 11 2012 Win64'  )
            c('vs2012_arm'  , 'Visual Studio 11 2012 ARM'    )
            c('vs2010'      , 'Visual Studio 10 2010' + _sfx )
            c('vs2010_32'   , 'Visual Studio 10 2010'        )
            c('vs2010_64'   , 'Visual Studio 10 2010 Win64'  )
            c('vs2010_ia64' , 'Visual Studio 10 2010 IA64'   )
            c('vs2008'      , 'Visual Studio 9 2008' + _sfx  )
            c('vs2008_32'   , 'Visual Studio 9 2008'         )
            c('vs2008_64'   , 'Visual Studio 9 2008 Win64'   )
            c('vs2008_ia64' , 'Visual Studio 9 2008 IA64'    )
            c('vs2005'      , 'Visual Studio 8 2005' + _sfx  )
            c('vs2005_32'   , 'Visual Studio 8 2005'         )
            c('vs2005_64'   , 'Visual Studio 8 2005 Win64'   )
            c('Visual Studio 15 2017' + _sfx , 'Visual Studio 15 2017' + _sfx )
            c('Visual Studio 15 2017'        , 'Visual Studio 15 2017'        )
            c('Visual Studio 15 2017 Win64'  , 'Visual Studio 15 2017 Win64'  )
            c('Visual Studio 15 2017 ARM'    , 'Visual Studio 15 2017 ARM'    )
            c('Visual Studio 14 2015' + _sfx , 'Visual Studio 14 2015' + _sfx )
            c('Visual Studio 14 2015'        , 'Visual Studio 14 2015'        )
            c('Visual Studio 14 2015 Win64'  , 'Visual Studio 14 2015 Win64'  )
            c('Visual Studio 14 2015 ARM'    , 'Visual Studio 14 2015 ARM'    )
            c('Visual Studio 12 2013' + _sfx , 'Visual Studio 12 2013' + _sfx )
            c('Visual Studio 12 2013'        , 'Visual Studio 12 2013'        )
            c('Visual Studio 12 2013 Win64'  , 'Visual Studio 12 2013 Win64'  )
            c('Visual Studio 12 2013 ARM'    , 'Visual Studio 12 2013 ARM'    )
            c('Visual Studio 11 2012' + _sfx , 'Visual Studio 11 2012' + _sfx )
            c('Visual Studio 11 2012'        , 'Visual Studio 11 2012'        )
            c('Visual Studio 11 2012 Win64'  , 'Visual Studio 11 2012 Win64'  )
            c('Visual Studio 11 2012 ARM'    , 'Visual Studio 11 2012 ARM'    )
            c('Visual Studio 10 2010' + _sfx , 'Visual Studio 10 2010' + _sfx )
            c('Visual Studio 10 2010'        , 'Visual Studio 10 2010'        )
            c('Visual Studio 10 2010 Win64'  , 'Visual Studio 10 2010 Win64'  )
            c('Visual Studio 10 2010 IA64'   , 'Visual Studio 10 2010 IA64'   )
            c('Visual Studio 9 2008' + _sfx  , 'Visual Studio 9 2008' + _sfx  )
            c('Visual Studio 9 2008'         , 'Visual Studio 9 2008'         )
            c('Visual Studio 9 2008 Win64'   , 'Visual Studio 9 2008 Win64'   )
            c('Visual Studio 9 2008 IA64'    , 'Visual Studio 9 2008 IA64'    )
            c('Visual Studio 8 2005' + _sfx  , 'Visual Studio 8 2005' + _sfx  )
            c('Visual Studio 8 2005'         , 'Visual Studio 8 2005'         )
            c('Visual Studio 8 2005 Win64'   , 'Visual Studio 8 2005 Win64'   )

        def test02_gen_to_name(self):
            def c(a, s):
                sc = VisualStudioInfo.to_name(a)
                if sc != s:
                    self.fail("{} should be '{}' but is '{}'".format(a, s, sc))

            c('Visual Studio 15 2017'        , 'vs2017_32'   )
            c('Visual Studio 15 2017 Win64'  , 'vs2017_64'   )
            c('Visual Studio 15 2017 ARM'    , 'vs2017_arm'  )
            c('Visual Studio 14 2015'        , 'vs2015_32'   )
            c('Visual Studio 14 2015 Win64'  , 'vs2015_64'   )
            c('Visual Studio 14 2015 ARM'    , 'vs2015_arm'  )
            c('Visual Studio 12 2013'        , 'vs2013_32'   )
            c('Visual Studio 12 2013 Win64'  , 'vs2013_64'   )
            c('Visual Studio 12 2013 ARM'    , 'vs2013_arm'  )
            c('Visual Studio 11 2012'        , 'vs2012_32'   )
            c('Visual Studio 11 2012 Win64'  , 'vs2012_64'   )
            c('Visual Studio 11 2012 ARM'    , 'vs2012_arm'  )
            c('Visual Studio 10 2010'        , 'vs2010_32'   )
            c('Visual Studio 10 2010 Win64'  , 'vs2010_64'   )
            c('Visual Studio 10 2010 IA64'   , 'vs2010_ia64' )
            c('Visual Studio 9 2008'         , 'vs2008_32'   )
            c('Visual Studio 9 2008 Win64'   , 'vs2008_64'   )
            c('Visual Studio 9 2008 IA64'    , 'vs2008_ia64' )
            c('Visual Studio 8 2005'         , 'vs2005_32'   )
            c('Visual Studio 8 2005 Win64'   , 'vs2005_64'   )
            c('vs2017'     , 'vs2017'      )
            c('vs2017_32'  , 'vs2017_32'   )
            c('vs2017_64'  , 'vs2017_64'   )
            c('vs2017_arm' , 'vs2017_arm'  )
            c('vs2015'     , 'vs2015'      )
            c('vs2015_32'  , 'vs2015_32'   )
            c('vs2015_64'  , 'vs2015_64'   )
            c('vs2015_arm' , 'vs2015_arm'  )
            c('vs2013'     , 'vs2013'      )
            c('vs2013_32'  , 'vs2013_32'   )
            c('vs2013_64'  , 'vs2013_64'   )
            c('vs2013_arm' , 'vs2013_arm'  )
            c('vs2012'     , 'vs2012'      )
            c('vs2012_32'  , 'vs2012_32'   )
            c('vs2012_64'  , 'vs2012_64'   )
            c('vs2012_arm' , 'vs2012_arm'  )
            c('vs2010'     , 'vs2010'      )
            c('vs2010_32'  , 'vs2010_32'   )
            c('vs2010_64'  , 'vs2010_64'   )
            c('vs2010_ia64', 'vs2010_ia64' )
            c('vs2008'     , 'vs2008'      )
            c('vs2008_32'  , 'vs2008_32'   )
            c('vs2008_64'  , 'vs2008_64'   )
            c('vs2008_ia64', 'vs2008_ia64' )
            c('vs2005'     , 'vs2005'      )
            c('vs2005_32'  , 'vs2005_32'   )
            c('vs2005_64'  , 'vs2005_64'   )

        def test03_parse_toolset(self):
            def t(spec, name_vs, ts_vs):
                cname_vs,cts_vs = VisualStudioInfo.sep_name_toolset(spec)
                if cname_vs != name_vs:
                    self.fail("{} should be '{}' but is '{}'".format(spec, name_vs, cname_vs))
                if cts_vs != ts_vs:
                    self.fail("{} should be '{}' but is '{}'".format(spec, ts_vs, cts_vs))
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
            t('vs2017_arm'            , 'vs2017_arm' , None           )
            t('vs2017_arm_clang'      , 'vs2017_arm' , 'v141_clang_c2')
            t('vs2017_arm_v141'       , 'vs2017_arm' , 'v141'         )
            t('vs2017_arm_v141_clang' , 'vs2017_arm' , 'v141_clang_c2')
            t('vs2017_arm_v140'       , 'vs2017_arm' , 'v140'         )
            t('vs2017_arm_v140_clang' , 'vs2017_arm' , 'v140_clang_c2')
            t('vs2017_arm_v120'       , 'vs2017_arm' , 'v120'         )
            t('vs2017_arm_v110'       , 'vs2017_arm' , 'v110'         )
            t('vs2017_arm_v100'       , 'vs2017_arm' , 'v100'         )
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
            t('vs2013'                , 'vs2013'     , None           )
            t('vs2013_xp'             , 'vs2013'     , 'v120_xp'      )
            t('vs2012'                , 'vs2012'     , None           )
            t('vs2012_xp'             , 'vs2012'     , 'v110_xp'      )
            t('vs2010'                , 'vs2010'     , None           )
            t('vs2010_xp'             , 'vs2010'     , 'v100_xp'      )

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    ut.main()

