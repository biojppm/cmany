#!/usr/bin/env python3

import unittest as ut
import subtest_fix

import os.path as osp
import tempfile

from c4.cmany.conf import Configs
from c4.cmany import conf
from c4.cmany.build_flags import BuildFlags

from ruamel import yaml as yaml
from ruamel.yaml.comments import CommentedMap as CommentedMap


# -----------------------------------------------------------------------------
def tmpfile(contents):
    fn = tempfile.mkstemp('.yml', 'cmany.')
    with open(fn, "w"):
        fn.write(contents)
    return fn


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test00ConfigsClass(ut.TestCase):

    def test00Empty(self):
        c = Configs()
        self.assertIsNotNone(c.get_val('project'))
        self.assertIsNotNone(c.get_val('config'))
        self.assertIsNotNone(c.get_val('flag_aliases'))

    def test01Load(self):
        c = Configs()
        c.load(text="foo: bar")
        self.assertIsNotNone(c.get_val('project'))
        self.assertIsNotNone(c.get_val('config'))
        self.assertIsNotNone(c.get_val('flag_aliases'))
        self.assertEqual(c.get_val('foo'), 'bar')

    def test02Merge(self):
        c1 = Configs()
        c1.load(text="""\
foo1: bar1
foo2: bar1
foo3: bar1
fonix:
  a: 1
  b: 1
  c: 1
  not_yet_another:
    a: 1
    b: 1
    c: 1
""")
        c2 = Configs()
        c2.load(text="""\
foo1: bar2
foo2: bar2
foo4: bar2
fonix:
  a: 2
  d: 2
  e: 2
  f: 2
  yet_another:
    a: 2
    d: 2
    e: 2
    f: 2
""")
        c1.merge_from(c2)
        self.assertEqual(c1.get_val('foo1'), 'bar2')
        self.assertEqual(c1.get_val('foo2'), 'bar2')
        self.assertEqual(c1.get_val('foo3'), 'bar1')
        self.assertEqual(c1.get_val('foo4'), 'bar2')
        self.assertEqual(c1.get_val('fonix.a'), 2)
        self.assertEqual(c1.get_val('fonix.b'), 1)
        self.assertEqual(c1.get_val('fonix.c'), 1)
        self.assertEqual(c1.get_val('fonix.d'), 2)
        self.assertEqual(c1.get_val('fonix.e'), 2)
        self.assertEqual(c1.get_val('fonix.f'), 2)
        self.assertEqual(c1.get_val('fonix.not_yet_another.a'), 1)
        self.assertEqual(c1.get_val('fonix.not_yet_another.b'), 1)
        self.assertEqual(c1.get_val('fonix.not_yet_another.c'), 1)
        self.assertEqual(c1.get_val('fonix.yet_another.a'), 2)
        self.assertEqual(c1.get_val('fonix.yet_another.d'), 2)
        self.assertEqual(c1.get_val('fonix.yet_another.e'), 2)
        self.assertEqual(c1.get_val('fonix.yet_another.f'), 2)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test01ConfigsFile(ut.TestCase):

    def test01ConfDirExists(self):
        self.assertTrue(osp.exists(conf.CONF_DIR))

    def test01ConfFileExists(self):
        fn = osp.join(conf.CONF_DIR, "cmany.yml")
        self.assertTrue(osp.exists(fn))

    def test02CanLoadConfFile(self):
        fn = osp.join(conf.CONF_DIR, "cmany.yml")
        c = Configs.load_seq((fn,))
        self.assertEqual(c.get_val('project'), {})

    def test03Set(self):
        fn = osp.join(conf.CONF_DIR, "cmany.yml")
        c = Configs.load_seq((fn,))
        self.assertIsNone(c.get_val("foo.bar.baz"))
        c.set_val("foo.bar.baz", 10)
        c.set_val("foo.bar.askdjaksjd", 11)
        self.assertEqual(c.get_val("foo.bar.baz"), 10)
        self.assertEqual(c.get_val("foo.bar.askdjaksjd"), 11)

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class BFTCase:
    @property
    def name(self):
        return self.__class__.__name__[7:].lower()
    def do_load(self):
        cm = yaml.load(self.__class__.yml, yaml.RoundTripLoader)
        if cm is None: cm = CommentedMap()
        bf = BuildFlags("")
        bf.load_config(cm)
        return bf
    def do_save(self):
        cm = CommentedMap()
        self.__class__.bf.save_config(cm)
        return cm
    def do_roundtrip_save_load(self):
        cm = CommentedMap()
        self.__class__.bf.save_config(cm)
        bf = BuildFlags("")
        bf.load_config(cm)
        return bf
    def do_roundtrip_load_save(self):
        cm = yaml.load(self.__class__.yml, yaml.RoundTripLoader)
        if cm is None: cm = CommentedMap()
        bf = BuildFlags("")
        bf.load_config(cm)
        cm = CommentedMap()
        bf.save_config(cm)
        return cm
    def check_bf(self, tstobj, bf):
        with tstobj.subTest(name=self.name, msg=self.name):
            self._check_bf(tstobj, bf)
    def check_cm(self, tstobj, cm):
        with tstobj.subTest(name=self.name, msg=self.name):
            self._check_cm(tstobj, cm)


class BFTCaseEmpty(BFTCase):
    bf = BuildFlags("empty")
    yml = ""
    def _check_bf(self, tstobj, bf):
        for a in BuildFlags.attrs:
            tstobj.assertTrue(not getattr(bf, a))
    def _check_cm(self, tstobj, cm):
        tstobj.assertTrue(not cm)


class BFTCaseCMakeVars(BFTCase):
    bf = BuildFlags("cmake_vars", cmake_vars=["VARFOO=BAR", "CMAKE_VERBOSE_MAKEFILE=1"])
    yml = """\
cmake_vars: VARFOO=BAR CMAKE_VERBOSE_MAKEFILE=1
"""
    non_empty = ("cmake_vars",)

    def _check_bf(self, tstobj, bf):
        tstobj.assertEqual(getattr(bf, "cmake_vars"), ["VARFOO=BAR", "CMAKE_VERBOSE_MAKEFILE=1"])
        for a in BuildFlags.attrs:
            if not a in __class__.non_empty:
                tstobj.assertTrue(not getattr(bf, a))

    def _check_cm(self, tstobj, cm):
        a = cm["cmake_vars"]
        a = BuildFlags.flag_str_to_list(a)
        tstobj.assertEqual(a, ["VARFOO=BAR", "CMAKE_VERBOSE_MAKEFILE=1"])
        for a in BuildFlags.attrs:
            if not a in __class__.non_empty:
                tstobj.assertTrue(not hasattr(cm, a))


bf_cases = (BFTCaseEmpty(), BFTCaseCMakeVars())

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test02BuildFlags(ut.TestCase):

    def test01Save(self):
        for cls in bf_cases:
            cm = cls.do_save()
            cls.check_cm(self, cm)

    def test02Load(self):
        for cls in bf_cases:
            bf = cls.do_load()
            cls.check_bf(self, bf)

    def test03RoundtripSaveLoad(self):
        for cls in bf_cases:
            bf = cls.do_roundtrip_save_load()
            cls.check_bf(self, bf)

    def test04RoundtripLoadSave(self):
        for cls in bf_cases:
            cm = cls.do_roundtrip_load_save()
            cls.check_cm(self, cm)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    ut.main()
