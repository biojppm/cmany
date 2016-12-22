import unittest as ut
from c4.pycmake import *
import os.path

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
if System.current_str() == 'windows':

    class TestVisualStudioInfo(ut.TestCase):

        def test00_instances(self):
            for k,v in VisualStudioInfo._versions.items():
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

        def test_find_any(self):
            any = VisualStudioInfo.find_any()
            self.assertIsNotNone(any)

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
if __name__ == '__main__':
    ut.main()
