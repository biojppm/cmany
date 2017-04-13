#!/usr/bin/env python3

import unittest as ut
import subtest_fix
import argparse
from collections import OrderedDict as odict

import c4.cmany as cmany
from c4.cmany import util, args as c4args
from c4.cmany import variant
from c4.cmany.project import CombinationRules

# utility variables for simpler names
ds = cmany.System.default_str()
da = cmany.Architecture.default_str()
dc = cmany.Compiler.default_str()
dt = cmany.BuildType.default_str()
dv = cmany.Variant.default_str()

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test10AsArguments(ut.TestCase):

    def t(self, input, expected_items, expected_combinations):
        if not hasattr(self, 'parser'):
            parser = argparse.ArgumentParser()
            c4args.add_select(parser)
            c4args.add_bundle_flags(parser)

        args = parser.parse_args(input)
        print(args)
        assert isinstance(expected_items, odict)

        for i in ('systems', 'architectures', 'compilers', 'build_types', 'variants'):
            expected = expected_items[i]
            actual = getattr(args, i)
            util.lognotice(i, "actual=", actual)
            util.lognotice(i, "expected=", expected)
            with self.subTest(msg="expected count of "+i, input=input):
                self.assertEqual(len(actual), len(expected))
            with self.subTest(msg="expected set of "+i, input=input):
                self.assertEqual(set(actual), set(expected))

        cr = []
        if hasattr(args, 'combination_rules'):
            cr = args.combination_rules
        cr = CombinationRules(cr)
        items = cr.valid_combinations(
            args.systems, args.architectures, args.compilers,
            args.build_types, args.variants)

    def test00(self):
        self.t(
            # args
            [],
            # expected items
            odict([
                ('systems', [ds]),
                ('architectures', [da]),
                ('compilers', [dc]),
                ('build_types', [dt]),
                ('variants', [dv])
            ]),
            # expected combinations
            [
                (ds, da, dc, dt, dv),
            ]
        )

    def test01(self):
        self.t(
            # args
            ["-a", "x86,x86_64", "-v", "none,'foo: -X wall','bar: -D BAR_DEF=1'"],
            # expected items
            odict([
                ('systems', [ds]),
                ('architectures', ['x86', 'x86_64']),
                ('compilers', [dc]),
                ('build_types', [dt]),
                ('variants', ['none', 'foo', 'bar'])
            ]),
            # expected combinations
            [
                (ds, 'x86', dc, dt, 'none'),
                (ds, 'x86', dc, dt, 'foo'),
                (ds, 'x86', dc, dt, 'var'),
                (ds, 'x86_64', dc, dt, 'none'),
                (ds, 'x86_64', dc, dt, 'foo'),
                (ds, 'x86_64', dc, dt, 'var'),
            ]
        )

        self.t(
            # args
            ["-a", "x86,x86_64", "--exclude-all", "foo.*64.*", "-v", "none,'foo: -X wall','bar: -D BAR_DEF=1 --exclude-all 64'"],
            # expected items
            odict([
                ('systems', [ds]),
                ('architectures', ['x86', 'x86_64']),
                ('compilers', [dc]),
                ('build_types', [dt]),
                ('variants', ['none', 'foo', 'bar'])
            ]),
            # expected combinations
            [
                (ds, 'x86', dc, dt, 'none'),
                (ds, 'x86', dc, dt, 'foo'),
                (ds, 'x86', dc, dt, 'var'),
                (ds, 'x86_64', dc, dt, 'none'),
                #(ds, 'x86_64', dc, dt, 'foo'), # excluded
                (ds, 'x86_64', dc, dt, 'var'),
            ]
        )


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    ut.main()
