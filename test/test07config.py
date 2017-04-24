#!/usr/bin/env python3

import unittest as ut
import subtest_fix

import os.path as osp
import tempfile

from c4.cmany.conf import Configs
from c4.cmany import conf


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

    def test00empty(self):
        c = Configs()
        self.assertIsNotNone(c.get_val('project'))
        self.assertIsNotNone(c.get_val('config'))
        self.assertIsNotNone(c.get_val('flag_aliases'))

    def test01load(self):
        c = Configs()
        c.load(text="foo: bar")
        print(c._dump)
        self.assertIsNotNone(c.get_val('project'))
        self.assertIsNotNone(c.get_val('config'))
        self.assertIsNotNone(c.get_val('flag_aliases'))
        self.assertEqual(c.get_val('foo'), 'bar')

    def test02merge(self):
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
        print("c1=", c1._dump)
        print("c2=", c2._dump)
        c1.merge_from(c2)
        print("c3=", c1._dump)
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
class Test00ConfigsFile(ut.TestCase):

    def test01conf_dir_exists(self):
        self.assertTrue(osp.exists(conf.CONF_DIR))

    def test01conf_file_exists(self):
        fn = osp.join(conf.CONF_DIR, "cmany.yml")
        self.assertTrue(osp.exists(fn))

    def test02can_load_conf_file(self):
        fn = osp.join(conf.CONF_DIR, "cmany.yml")
        c = Configs.load_seq((fn,))
        self.assertEqual(c.get_val('project'), {})
        print(c.get_val('config'))
        print(c.get_val('project'))

    def test03set(self):
        fn = osp.join(conf.CONF_DIR, "cmany.yml")
        c = Configs.load_seq((fn,))
        c.set_val("foo.bar.baz", 10)
        c.set_val("foo.bar.askdjaksjd", 11)
        print(c.get_val("foo"))
        print(c._dump)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    ut.main()
