#!/usr/bin/env python3

import unittest as ut
import tempfile
import os
from collections import OrderedDict as odict

import c4.cmany.flags as flags


#------------------------------------------------------------------------------
class Test00FlagState(ut.TestCase):

    def test00CompilersShouldBeListedInFlags(self):
        for tcn, (comps, cflags, yml) in test_cases.items():
            with self.subTest(test_case=tcn):
                for k, v in cflags.items():
                    for c in comps:
                        self.assertTrue(c in v.compilers, str(c) + " is not listed in " + str(v.compilers))


#------------------------------------------------------------------------------
class Test01Dump(ut.TestCase):

    def test(self):
        for tcn, (comps, cflags, yml) in test_cases.items():
            with self.subTest(test_case=tcn):
                txt = flags.dump_yml(comps, cflags)
                self.assertEqual(yml, txt, tcn)


#------------------------------------------------------------------------------
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
        yml = """compilers: [gcc, clang, icc, vs]
---
c++11:
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


#------------------------------------------------------------------------------
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
                compsv, cflagsv = flags.merge(comps2, cflags2, comps1, cflags1)
                ymlv = flags.dump_yml(compsv, cflagsv)
                self.assertTrue(same_elements_in_list(compsv, compsr), tcn)
                self.assertEqual(compsv, compsr, tcn)
                self.assertEqual(ymlv, ymlr, tcn)


#------------------------------------------------------------------------------
class Test04FlagsIO(ut.TestCase):

    def setUp(self):
        flags.load_known_flags()

    def test00SavedIsSameAsOriginal(self):
        for tcn, (rcomps, rflags, yml) in test_cases.items():
            with self.subTest(test_case=tcn):
                fh_, fn = tmpfile()
                fh = os.fdopen(fh_)
                flags.save(rcomps, rflags, fn)
                c, f = flags.load(fn)
                self.assertEqual(c, rcomps)
                self.assertEqual(len(f), len(rflags))
                self.assertEqual(list(f.keys()), list(rflags.keys()))
                for (rname, rf), (vname, vf) in zip(rflags.items(), f.items()):
                    self.assertEqual(rcomps, vf.compilers)
                    for kc in flags.known_compilers:
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
                flags.save(rcomps, rflags, fn)
                c, f = flags.load(fn)
                flags.save(c, f, fn_out)
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


#------------------------------------------------------------------------------
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


#------------------------------------------------------------------------------

def tc(name, comps, flags, **kwargs):
    yml = kwargs['yml']
    d_ = (name, (comps, flags, yml))
    return d_

def d(*args):
    return odict([*args])

def f(name, *args, **kwargs):
    return name, flags.CFlag(name, *args, **kwargs)

from c4.cmany import conf
kc, kf = flags.load(conf.KNOWN_FLAGS_FILE)
kyml = flags.dump_yml(kc, kf)

test_cases = d(

    tc('gcc-g', ['gcc'], d(f('g', gcc='-g')),
yml="""compilers: [gcc]
---
g:
    gcc: -g
"""),

    tc('gcc-g3', ['gcc'], d(f('g3', gcc='-g3')),
yml="""compilers: [gcc]
---
g3:
    gcc: -g3
"""),

    tc('clang-g3', ['clang'], d(f('g3', clang='-g3')),
       yml="""compilers: [clang]
---
g3:
    clang: -g3
"""),

    tc('gcc, clang-g3', ['gcc', 'clang'], d(f('g3', gcc='-g3', clang='-g3')),
       yml="""compilers: [gcc, clang]
---
g3:
    gcc,clang: -g3
"""),

    tc('clang, gcc-g3', ['clang', 'gcc'], d(f('g3', clang='-g3', gcc='-g3')),
       yml="""compilers: [clang, gcc]
---
g3:
    clang,gcc: -g3
"""),

    tc('known_flags', kc, kf, yml=kyml)
)
