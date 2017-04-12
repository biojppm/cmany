#!/usr/bin/env python3

import unittest as ut
import subtest_fix
import argparse
from collections import OrderedDict as odict

import c4.cmany as cmany
from c4.cmany import util, args as c4args
from c4.cmany import variant
from c4.cmany import build_item


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test10AsArguments(ut.TestCase):

    @staticmethod
    def count(subject):
        c = 1
        for i in ('systems', 'architectures', 'compilers', 'build_types', 'variants'):
            if not isinstance(subject, odict):
                ai = getattr(subject, i)
            else:
                ai = subject.get(i)
            c = c * len(ai)
        return c

    def t(self, input, expected_items):
        parser = argparse.ArgumentParser()
        c4args.add_select(parser)
        c4args.add_bundle_flags(parser)
        args = parser.parse_args(input)
        assert isinstance(expected_items, odict)

        expected_count = __class__.count(expected_items)
        actual_count = __class__.count(args)
        with self.subTest(input=input, msg="expected count"):
            self.assertEqual(actual_count, expected_count)

        # for k, refval in expected_props.items():
        #     result = getattr(var.flags, k)
        #     with self.subTest(input=input, which_var=which_var, desc='variant properties', prop=k):
        #         self.assertEqual(result, refval, msg='property: ' + k)

    def test00(self):
        self.t([],
               odict([
                   ('systems', [cmany.System.default()]),
                   ('architectures', [cmany.Architecture.default()]),
                   ('compilers', [cmany.Compiler.default()]),
                   ('build_types', [cmany.BuildType.default()]),
                   ('variants', [])
               ]))

        self.t(["-a", "x86,x86_64", "-v", "none,'foo: -X wall','bar: -D BAR_DEF=1'"],
               odict([
                   ('systems', [cmany.System.default()]),
                   ('architectures', ['x86', 'x86_64']),
                   ('compilers', [cmany.Compiler.default()]),
                   ('build_types', [cmany.BuildType.default()]),
                   ('variants', ['none', 'foo', 'bar'])
               ]))

        return
        self.t(["-a", "x86,x86_64", "-v", "none,'foo: -X wall --exclude-all 64','bar: -D BAR_DEF=1 --exclude-all 64'"],
               odict([
                   ('systems', [cmany.System.default()]),
                   ('architectures', ['x86', 'x86_64']),
                   ('compilers', [cmany.Compiler.default()]),
                   ('build_types', [cmany.BuildType.default()]),
                   ('variants', ['none', 'foo'])
               ]))


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    ut.main()
