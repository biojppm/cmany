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
class ConfFixtureBase(ut.TestCase):
    """base class for config test cases"""

    def do_load(self):
        cm = self.cm.copy()
        bf = BuildFlags("")
        bf.load_config(cm)
        return bf

    def do_save(self):
        cm = CommentedMap()
        self.bf.save_config(cm)
        return cm

    def do_roundtrip_save_load(self):
        cm = CommentedMap()
        self.bf.save_config(cm)
        bf = BuildFlags("")
        bf.load_config(cm)
        return bf

    def do_roundtrip_load_save(self):
        bf = BuildFlags("")
        bf.load_config(self.cm)
        cm = CommentedMap()
        bf.save_config(cm)
        return cm


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Test cases for build flags

# using the _ prefix prevents unittest from instantiating tests for this class
class _BFTCase(ConfFixtureBase):
    """base for build flags test case"""

    def _setUp(self, bf, yml):
        self.bf = bf
        self.yml = yml
        self.name = self.__class__.__name__[7:].lower()
        YAML = yaml.YAML()
        self.cm = YAML.load(self.yml)
        if self.cm is None:
            self.cm = CommentedMap()
        self.non_empty = []
        for a in BuildFlags.attrs:
            if getattr(bf, a):
                self.non_empty.append(a)

    def check_bf(self, bf):
        with self.subTest(name=self.name, msg=self.name):
            for a in self.non_empty:
                self.assertEqual(getattr(bf, a), getattr(self.bf, a))
            for a in BuildFlags.attrs:
                if a not in self.non_empty:
                    self.assertTrue(not getattr(bf, a))

    def check_cm(self, cm):
        with self.subTest(name=self.name, msg=self.name):
            for a in self.non_empty:
                v = cm[a]
                if a != 'toolchain':
                    v = BuildFlags.flag_str_to_list(v)
                self.assertEqual(v, getattr(self.bf, a))
            for a in BuildFlags.attrs:
                if a not in self.non_empty:
                    self.assertTrue(not hasattr(cm, a))

    def test01Save(self):
        cm = self.do_save()
        self.check_cm(cm)

    def test02Load(self):
        bf = self.do_load()
        self.check_bf(bf)

    def test03RoundtripSaveLoad(self):
        bf = self.do_roundtrip_save_load()
        self.check_bf(bf)

    def test04RoundtripLoadSave(self):
        cm = self.do_roundtrip_load_save()
        self.check_cm(cm)


# -----------------------------------------------------------------------------
class Test02BuildFlags01Empty(_BFTCase):
    def setUp(self):
        self._setUp(bf=BuildFlags("empty"), yml="")


class Test02BuildFlags02CMakeVars(_BFTCase):
    def setUp(self):
        super()._setUp(
            bf=BuildFlags("cmake_vars",
                          cmake_vars=["VARFOO=BAR", "CMAKE_VERBOSE_MAKEFILE=1"]),
            yml="""\
cmake_vars: VARFOO=BAR CMAKE_VERBOSE_MAKEFILE=1
""")


class Test02BuildFlags03CMakeVarsAndCxxflags(_BFTCase):
    def setUp(self):
        self._setUp(
            bf=BuildFlags("cmake_vars_and_cxxflags",
                          cmake_vars=["VARFOO=BAR", "CMAKE_VERBOSE_MAKEFILE=1"],
                          cxxflags=["-std=c++11", "-Wall", ]),
            yml="""\
cmake_vars: VARFOO=BAR CMAKE_VERBOSE_MAKEFILE=1
cxxflags: -std=c++11 -Wall
""")


class Test02BuildFlags04Full(_BFTCase):
    def setUp(self):
        self._setUp(
            bf=BuildFlags("cmake_vars_and_cxxflags",
                          cmake_vars=["VARFOO=BAR", "CMAKE_VERBOSE_MAKEFILE=1"],
                          defines=["FOO", "BAR", "VFOO=baaaaaaaaaa"],
                          cflags=["-std=c++11", "-Wall", ],
                          cxxflags=["-std=c++11", "-Wall", ],
                          toolchain="somefile.cmake"),
            yml="""\
cmake_vars: VARFOO=BAR CMAKE_VERBOSE_MAKEFILE=1
defines: FOO BAR VFOO=baaaaaaaaaa
cflags: -std=c++11 -Wall
cxxflags: -std=c++11 -Wall
toolchain: somefile.cmake
""")


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    ut.main()
