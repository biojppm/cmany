#!/usr/bin/env python3

import unittest as ut
import subtest_fix
import tempfile
import os
import argparse
from collections import OrderedDict as odict

from c4.cmany import conf,  flags, util, args as c4args


# -----------------------------------------------------------------------------
class Test00FlagState(ut.TestCase):

    def test00CompilersShouldBeListedInFlags(self):
        for tcn, (comps, cflags, yml) in test_cases.items():
            with self.subTest(test_case=tcn):
                for k, v in cflags.items():
                    for c in comps:
                        self.assertTrue(c in v.compilers, str(c) + " is not listed in " + str(v.compilers))


# -----------------------------------------------------------------------------
class Test01Dump(ut.TestCase):

    def test(self):
        for tcn, (comps, cflags, yml) in test_cases.items():
            with self.subTest(test_case=tcn):
                txt = flags.dump_yml(comps, cflags)
                self.assertEqual(yml, txt, tcn)


# -----------------------------------------------------------------------------
class Test02Load(ut.TestCase):

    def test00RunTestCases(self):
        for tcn, (rcomps, rflags, yml) in test_cases.items():
            with self.subTest(test_case=tcn):
                (comps, cflags) = flags.load_yml(yml)
                #print()
                #print(tcn, rcomps, comps)
                #print(tcn, rflags, cflags)
                #for (k1, v1), (k2, v2) in zip(rflags.items(), cflags.items()):
                #    print(tcn, "k1v1", k1, v1)
                #    print(tcn, "k2v2", k2, v2)
                #    for c1, c2 in zip(v1.compilers, v2.compilers):
                #        print(tcn, "comp", c1, c2)
                self.assertEqual(comps, rcomps, tcn)
                self.assertTrue(same_flags(cflags, rflags), tcn)

    def test01DoCommasWork(self):
        yml = """c++11:
    gcc,clang,icc: -std=c++11
    vs: ''
"""
        c, f = flags.load_yml(yml)
        self.assertTrue('c++11' in f)
        f11 = f['c++11']
        self.assertTrue(hasattr(f11, 'gcc'))
        self.assertTrue(hasattr(f11, 'icc'))
        self.assertTrue(hasattr(f11, 'clang'))
        self.assertEqual(f11.gcc, '-std=c++11')
        self.assertEqual(f11.icc, '-std=c++11')
        self.assertEqual(f11.clang, '-std=c++11')


# -----------------------------------------------------------------------------
class Test03Merge(ut.TestCase):

    def test(self):
        self._run('gcc-g3', 'clang-g3', 'gcc, clang-g3', 'clang, gcc-g3')

    def _run(self, tc1, tc2, r1into2, r2into1):
        for v1, v2, ref in ((tc1, tc2, r1into2), (tc2, tc1, r2into1)):
            tcn = "merge " + v1 + " into " + v2 + ": should be same as " + ref
            with self.subTest(test_case=tcn):
                comps1, cflags1, yml1 = test_cases[v1]
                comps2, cflags2, yml2 = test_cases[v2]
                compsr, cflagsr, ymlr = test_cases[ref]
                cflagsv = flags.merge(cflags2, cflags1)
                compsv = flags.get_all_compilers(cflagsv)
                ymlv = flags.dump_yml(compsv, cflagsv)
                self.assertTrue(same_elements_in_list(compsv, compsr), tcn)
                self.assertEqual(compsv, compsr, tcn)
                self.assertEqual(ymlv, ymlr, tcn)


# -----------------------------------------------------------------------------
class Test04FlagsIO(ut.TestCase):

    def setUp(self):
        with open(os.path.join(conf.CONF_DIR, "cmany.yml"), "r") as f:
            self.comps, self.flags = flags.load_yml(f.read())

    @staticmethod
    def _do_save(comps_, flags_, filename):
        with open(filename, 'w') as f:
            yml = flags.dump_yml(comps_, flags_)
            f.write(yml)

    @staticmethod
    def _do_load(filename):
        with open(filename, 'r') as f:
            yml = f.read()
            comps_, flags_ = flags.load_yml(yml)
        return comps_, flags_

    def test00SavedIsSameAsOriginal(self):
        for tcn, (rcomps, rflags, yml) in test_cases.items():
            with self.subTest(test_case=tcn):
                fh_, fn = tmpfile()
                fh = os.fdopen(fh_)
                __class__._do_save(rcomps, rflags, fn)
                c, f = __class__._do_load(fn)
                self.assertEqual(c, rcomps)
                self.assertEqual(len(f), len(rflags))
                self.assertEqual(list(f.keys()), list(rflags.keys()))
                for (rname, rf), (vname, vf) in zip(rflags.items(), f.items()):
                    self.assertEqual(rcomps, vf.compilers)
                    for kc in self.comps:
                        #print(rname, c, rf.get(c), vf.get(c))
                        self.assertEqual(rf.get(kc), vf.get(kc))
                fh.close()
                os.remove(fn)
                del fh

    def test01WriteReadWriteIsSame(self):
        for tcn, (rcomps, rflags, yml) in test_cases.items():
            with self.subTest(test_case=tcn):
                frefh, fn = tmpfile()
                fvalh, fn_out = tmpfile()
                fref = os.fdopen(frefh)
                fval = os.fdopen(fvalh)
                __class__._do_save(rcomps, rflags, fn)
                c, f = __class__._do_load(fn)
                __class__._do_save(c, f, fn_out)
                ref = list(fref.readlines())
                val = list(fval.readlines())
                lr = len(ref)
                lv = len(val)
                self.assertEqual(lr, lv)
                for i in range(0, max(lr, lv)):
                    if i < lr and i < lv:
                        self.assertEqual(ref[i], val[i])
                    else:
                        break
                del fref, frefh
                del fval, fvalh
                os.remove(fn)
                os.remove(fn_out)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test10Flags(ut.TestCase):

    def test01_cmake_vars(self):
        self._do_separate_test('-V', '--cmake-vars')

    def test02_defines(self):
        self._do_separate_test('-D', '--defines')

    def test03_cxxflags(self):
        self._do_separate_test('-X', '--cxxflags')

    def test04_cflags(self):
        self._do_separate_test('-C', '--cflags')

    def _do_separate_test(self, shortopt, longopt):
        n = longopt[2:]
        for o in (shortopt, longopt):
            def _c(a, r): self.check_one(n, o, a, r)

            _c('{} VAR1', ['VAR1'])
            _c('{} VAR2,VAR3', ['VAR2', 'VAR3'])
            _c('{} VAR4 {} VAR5', ['VAR4', 'VAR5'])
            _c('{} VAR6,VAR7 {} VAR8,VAR9', ['VAR6', 'VAR7', 'VAR8', 'VAR9'])
            _c('{} VAR\,1', ['VAR,1'])
            _c('{} VAR\,2,VAR\,3', ['VAR,2', 'VAR,3'])
            _c('{} VAR\,4 {} VAR\,5', ['VAR,4', 'VAR,5'])
            _c('{} VAR\,6,VAR\,7 {} VAR\,8,VAR\,9', ['VAR,6', 'VAR,7', 'VAR,8', 'VAR,9'])
            _c('{} VAR1=1', ['VAR1=1'])
            _c('{} VAR2=2,VAR3=3', ['VAR2=2', 'VAR3=3'])
            _c('{} VAR4=4 {} VAR5=5', ['VAR4=4', 'VAR5=5'])
            _c('{} VAR6=6,VAR7=7 {} VAR8=8,VAR9=9', ['VAR6=6', 'VAR7=7', 'VAR8=8', 'VAR9=9'])
            _c('{} VAR1=1\,a', ['VAR1=1,a'])
            _c('{} VAR2=2\,a,VAR3=3\,a', ['VAR2=2,a', 'VAR3=3,a'])
            _c('{} VAR4=4\,a {} VAR5=5\,a', ['VAR4=4,a', 'VAR5=5,a'])
            _c('{} VAR6=6\,a,VAR7=7\,a {} VAR8=8\,a,VAR9=9\,a',
               ['VAR6=6,a', 'VAR7=7,a', 'VAR8=8,a', 'VAR9=9,a'])
            _c(['{}', 'VAR1="1 with spaces"'], ['VAR1="1 with spaces"'])
            _c(['{}', 'VAR2="2 with spaces",VAR3="3 with spaces"'],
               ['VAR2="2 with spaces"', 'VAR3="3 with spaces"'])
            _c(['{}', 'VAR4="4 with spaces"', '{}', 'VAR5="5 with spaces"'],
               ['VAR4="4 with spaces"', 'VAR5="5 with spaces"'])
            _c(['{}', 'VAR6="6 with spaces",VAR7="7 with spaces"', '{}',
                'VAR8="8 with spaces",VAR9="9 with spaces"'],
               ['VAR6="6 with spaces"', 'VAR7="7 with spaces"', 'VAR8="8 with spaces"',
                'VAR9="9 with spaces"'])
            _c(['{}', 'VAR1="1\,a with spaces"'], ['VAR1="1,a with spaces"'])
            _c(['{}', 'VAR2="2\,a with spaces",VAR3="3\,a with spaces"'],
               ['VAR2="2,a with spaces"', 'VAR3="3,a with spaces"'])
            _c(['{}', 'VAR4="4\,a with spaces"', '{}', 'VAR5="5\,a with spaces"'],
               ['VAR4="4,a with spaces"', 'VAR5="5,a with spaces"'])
            _c(['{}', 'VAR6="6\,a with spaces",VAR7="7\,a with spaces"', '{}',
                'VAR8="8\,a with spaces",VAR9="9\,a with spaces"'],
               ['VAR6="6,a with spaces"', 'VAR7="7,a with spaces"', 'VAR8="8,a with spaces"',
                'VAR9="9,a with spaces"'])
            _c('{} "-fPIC,-Wall,-O3,-Os"', ['-fPIC', '-Wall', '-O3', '-Os'])
            _c("{} '-fPIC,-Wall,-O3,-Os'", ['-fPIC', '-Wall', '-O3', '-Os'])
            _c('{} "-fPIC","-Wall","-O3","-Os"', ['-fPIC', '-Wall', '-O3', '-Os'])
            _c("{} '-fPIC','-Wall','-O3','-Os'", ['-fPIC', '-Wall', '-O3', '-Os'])

    def check_one(self, name, opt, args, ref):
        if isinstance(args, str):
            args = args.split(' ')
        args_ = args
        args = []
        for a in args_:
            args.append(a.format(opt))
        p = argparse.ArgumentParser()
        c4args.add_bundle_flags(p)
        out = p.parse_args(args)
        # print(out, kwargs)
        a = getattr(out, name)
        self.assertEqual(ref, a)
        del out

    def check_many(self, args, **ref):
        if isinstance(args, str):
            args = util.splitesc_quoted(args, ' ')
        p = argparse.ArgumentParser()
        c4args.add_bundle_flags(p)
        out = p.parse_args(args)
        # print(out, kwargs)
        for k, refval in ref.items():
            result = getattr(out, k)
            self.assertEqual(result, refval)
        del out

    def test10_mixed0(self):
        self.check_many('-X "-fPIC" -D VARIANT1', vars=[], cxxflags=['-fPIC'], cflags=[],
                        defines=['VARIANT1'])
        self.check_many('-X "-Wall" -D VARIANT2', vars=[], cxxflags=['-Wall'], cflags=[],
                        defines=['VARIANT2'])
        self.check_many('-X nortti,c++14 -D VARIANT3', vars=[], cxxflags=['nortti', 'c++14'], cflags=[],
                        defines=['VARIANT3'])
        self.check_many('-X "-fPIC,-Wl\,-rpath" -D VARIANT1', vars=[], cxxflags=['-fPIC', '-Wl,-rpath'],
                        cflags=[], defines=['VARIANT1'])

    def test11_mixed1(self):
        self.check_many('-X "-fPIC" -D VARIANT1,VARIANT_TYPE=1', vars=[], cxxflags=['-fPIC'], cflags=[],
                        defines=['VARIANT1', 'VARIANT_TYPE=1'])
        self.check_many('-X "-Wall" -D VARIANT2,VARIANT_TYPE=2', vars=[], cxxflags=['-Wall'], cflags=[],
                        defines=['VARIANT2', 'VARIANT_TYPE=2'])
        self.check_many('-X nortti,c++14 -D VARIANT3,VARIANT_TYPE=3', vars=[], cxxflags=['nortti', 'c++14'],
                        cflags=[], defines=['VARIANT3', 'VARIANT_TYPE=3'])

    def test12_mixed2(self):
        self.check_many('-X "-fPIC" -D VARIANT1,"VARIANT_TYPE=1"', vars=[], cxxflags=['-fPIC'], cflags=[],
                        defines=['VARIANT1', 'VARIANT_TYPE=1'])
        self.check_many('-X "-Wall" -D VARIANT2,"VARIANT_TYPE=2"', vars=[], cxxflags=['-Wall'], cflags=[],
                        defines=['VARIANT2', 'VARIANT_TYPE=2'])
        self.check_many('-X nortti,c++14 -D VARIANT3,"VARIANT_TYPE=3"', vars=[],
                        cxxflags=['nortti', 'c++14'], cflags=[], defines=['VARIANT3', 'VARIANT_TYPE=3'])

    def test13_mixed3(self):
        self.check_many('-X "-fPIC" -D "VARIANT1,VARIANT_TYPE=1"', vars=[], cxxflags=['-fPIC'], cflags=[],
                        defines=['VARIANT1', 'VARIANT_TYPE=1'])
        self.check_many('-X "-Wall" -D "VARIANT2,VARIANT_TYPE=2"', vars=[], cxxflags=['-Wall'], cflags=[],
                        defines=['VARIANT2', 'VARIANT_TYPE=2'])
        self.check_many('-X nortti,c++14 -D "VARIANT3,VARIANT_TYPE=3"', vars=[],
                        cxxflags=['nortti', 'c++14'], cflags=[], defines=['VARIANT3', 'VARIANT_TYPE=3'])


# -----------------------------------------------------------------------------
def tmpfile():
    return tempfile.mkstemp('.yml', 'cmany_flags-')


def same_elements_in_list(l1, l2):
    for k1, k2 in zip(l1, l2):
        if not (k1 in l2):
            return False
        if not (k2 in l1):
            return False
    return True


def same_flags(f1, f2):
    if len(f1) != len(f2):
        return False
    if not same_elements_in_list(f1.keys(), f2.keys()):
        return False
    for (f1n, f1v), (f2n, f2v) in zip(f1.items(), f2.items()):
        if not same_elements_in_list(f1v.compilers, f2v.compilers):
            return False
        for c in f1v.compilers:
            if f1v.get(c) != f2v.get(c):
                return False
    return True


# -----------------------------------------------------------------------------

def tc(name, comps, flags, **kwargs):
    yml = kwargs['yml']
    d_ = (name, (comps, flags, yml))
    return d_


def d(*args):
    l = list(args)
    return odict(l)


def f(name, *args, **kwargs):
    return name, flags.CFlag(name, *args, **kwargs)


with open(os.path.join(conf.CONF_DIR, "cmany.yml")) as fconf:
    kc, kf = flags.load_yml(fconf.read())
kyml = flags.dump_yml(kc, kf)

test_cases = d(

    tc('gcc-g', ['gcc'], d(f('g', gcc='-g')), yml="""g:
    gcc: -g
"""),

    tc('gcc-g3', ['gcc'], d(f('g3', gcc='-g3')), yml="""g3:
    gcc: -g3
"""),

    tc('clang-g3', ['clang'], d(f('g3', clang='-g3')), yml="""g3:
    clang: -g3
"""),

    tc('gcc, clang-g3', ['gcc', 'clang'], d(f('g3', gcc='-g3', clang='-g3')), yml="""g3:
    gcc,clang: -g3
"""),

    tc('clang, gcc-g3', ['clang', 'gcc'], d(f('g3', clang='-g3', gcc='-g3')), yml="""g3:
    clang,gcc: -g3
"""),

    tc('known_flags', kc, kf, yml=kyml)
)
