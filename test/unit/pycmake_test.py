import unittest as ut
from c4.pycmake import *
import os.path

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
if System.current_str() == 'windows':

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
                    self.fail("{} should be '{}' but is '{}".format(a, s, sc))
            _sfx = " Win64" if Architecture.current().is64 else ""
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
            c('vs2008'      , 'Visual Studio 8 2008' + _sfx  )
            c('vs2008_32'   , 'Visual Studio 8 2008'         )
            c('vs2008_64'   , 'Visual Studio 8 2008 Win64'   )
            c('vs2008_ia64' , 'Visual Studio 8 2008 IA64'    )
            c('vs2005'      , 'Visual Studio 5 2005' + _sfx  )
            c('vs2005_32'   , 'Visual Studio 5 2005'         )
            c('vs2005_64'   , 'Visual Studio 5 2005 Win64'   )
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
            c('Visual Studio 8 2008' + _sfx  , 'Visual Studio 8 2008' + _sfx  )
            c('Visual Studio 8 2008'         , 'Visual Studio 8 2008'         )
            c('Visual Studio 8 2008 Win64'   , 'Visual Studio 8 2008 Win64'   )
            c('Visual Studio 8 2008 IA64'    , 'Visual Studio 8 2008 IA64'    )
            c('Visual Studio 5 2005' + _sfx  , 'Visual Studio 5 2005' + _sfx  )
            c('Visual Studio 5 2005'         , 'Visual Studio 5 2005'         )
            c('Visual Studio 5 2005 Win64'   , 'Visual Studio 5 2005 Win64'   )

        def test02_gen_to_name(self):
            def c(a, s):
                sc = VisualStudioInfo.to_name(a)
                if sc != s:
                    self.fail("{} should be '{}' but is '{}".format(a, s, sc))

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
            c('Visual Studio 8 2008'         , 'vs2008_32'   )
            c('Visual Studio 8 2008 Win64'   , 'vs2008_64'   )
            c('Visual Studio 8 2008 IA64'    , 'vs2008_ia64' )
            c('Visual Studio 5 2005'         , 'vs2005_32'   )
            c('Visual Studio 5 2005 Win64'   , 'vs2005_64'   )
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

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
if __name__ == '__main__':
    ut.main()
