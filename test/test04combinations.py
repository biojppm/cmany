#!/usr/bin/env python3

import unittest as ut
import subtest_fix
import argparse
from collections import OrderedDict as odict

import c4.cmany as cmany
from c4.cmany import util, args as c4args
from c4.cmany.project import CombinationRules

# utility variables for simpler names
ds = cmany.System.default_str()
da = cmany.Architecture.default_str()
dc = cmany.Compiler.default_str()
dt = cmany.BuildType.default_str()
dv = cmany.Variant.default_str()

vnone = 'none'
vfoo = 'foo: -X wall'
vbar = 'bar: -D BAR_DEF=1'
vspec = "'{}','{}','{}'".format(vnone, vfoo, vbar)

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test10AsArguments(ut.TestCase):

    def t(self, input, expected_items, expected_combinations):
        assert isinstance(expected_items, odict)
        if not hasattr(self, 'parser'):
            parser = argparse.ArgumentParser()
            c4args.add_select(parser)
            c4args.add_bundle_flags(parser)

        args = parser.parse_args(input)
        # util.logcmd(args)

        for i in ('systems', 'architectures', 'compilers', 'build_types', 'variants'):
            expected = expected_items[i]
            actual = getattr(args, i)
            # print(i, "actual=", actual)
            # print(i, "expected=", expected)
            with self.subTest(msg="expected count of "+i, input=input):
                self.assertEqual(len(actual), len(expected))
            with self.subTest(msg="expected list of "+i, input=input):
                self.assertEqual(actual, expected)

        # expected combinations (constructed with their types)
        expected_combinations = [(
            cmany.System(s),
            cmany.Architecture(a),
            cmany.Compiler(c),
            cmany.BuildType(t),
            cmany.Variant(v)
        ) for s, a, c, t, v in expected_combinations]

        # actual combinations
        s, a, c, t, v = cmany.Project.get_build_items(**vars(args))
        cr = []
        if hasattr(args, 'combination_rules'):
            cr = args.combination_rules
        cr = CombinationRules(cr)
        actual_combinations = cr.valid_combinations(s, a, c, t, v)

        # print("expected_combinations", expected_combinations)
        # print("actual_combinations", actual_combinations)
        with self.subTest(msg="expected count of combinations", input=input):
            self.assertEqual(len(expected_combinations), len(actual_combinations))
        for exp, act in zip(expected_combinations, actual_combinations):
            with self.subTest(msg="combination architecture", input=input):
                self.assertEqual(act[0].name, exp[0].name)
            with self.subTest(msg="combination system", input=input):
                self.assertEqual(act[1].name, exp[1].name)
            with self.subTest(msg="combination compiler", input=input):
                self.assertEqual(act[2].name, exp[2].name)
            with self.subTest(msg="combination build type", input=input):
                self.assertEqual(act[3].name, exp[3].name)
            with self.subTest(msg="combination variant", input=input):
                self.assertEqual(act[4].name, exp[4].name)

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
            ["-a", "x86,x86_64", "-v", vspec],
            # expected items
            odict([
                ('systems', [ds]),
                ('architectures', ['x86', 'x86_64']),
                ('compilers', [dc]),
                ('build_types', [dt]),
                ('variants', [vnone, vfoo, vbar])
            ]),
            # expected combinations
            [
                (ds, 'x86', dc, dt, vnone),
                (ds, 'x86', dc, dt, vfoo),
                (ds, 'x86', dc, dt, vbar),
                (ds, 'x86_64', dc, dt, vnone),
                (ds, 'x86_64', dc, dt, vfoo),
                (ds, 'x86_64', dc, dt, vbar),
            ]
        )

    def test02(self):
        rules = "x86_64.*foo"
        args = ["-a", "x86,x86_64", "-v", vspec]
        expected_items = odict([
            ('systems', [ds]),
            ('architectures', ['x86', 'x86_64']),
            ('compilers', [dc]),
            ('build_types', [dt]),
            ('variants', [vnone, vfoo, vbar])
        ])
        expected_combinations_exc = [
            (ds, 'x86', dc, dt, vnone),
            (ds, 'x86', dc, dt, vfoo),
            (ds, 'x86', dc, dt, vbar),
            (ds, 'x86_64', dc, dt, vnone),
            # (ds, 'x86_64', dc, dt, vfoo),
            (ds, 'x86_64', dc, dt, vbar),
        ]
        expected_combinations_inc = [
            # (ds, 'x86', dc, dt, vnone),
            # (ds, 'x86', dc, dt, vfoo),
            # (ds, 'x86', dc, dt, vbar),
            # (ds, 'x86_64', dc, dt, vnone),
            (ds, 'x86_64', dc, dt, vfoo),
            # (ds, 'x86_64', dc, dt, vbar),
        ]
        self.t(args + ["--exclude-builds", rules], expected_items,
               expected_combinations_exc)
        self.t(args + ["--exclude-builds-all", rules], expected_items,
               expected_combinations_exc)
        self.t(args + ["--include-builds", rules], expected_items,
               expected_combinations_inc)
        self.t(args + ["--include-builds-all", rules], expected_items,
               expected_combinations_inc)

    def test03(self):
        rules = "x86-.*foo"
        args = ["-a", "x86,x86_64", "-v", vspec]
        expected_items = odict([
            ('systems', [ds]),
            ('architectures', ['x86', 'x86_64']),
            ('compilers', [dc]),
            ('build_types', [dt]),
            ('variants', [vnone, vfoo, vbar])
        ])
        expected_combinations_exc = [
            (ds, 'x86', dc, dt, vnone),
            # (ds, 'x86', dc, dt, vfoo),
            (ds, 'x86', dc, dt, vbar),
            (ds, 'x86_64', dc, dt, vnone),
            (ds, 'x86_64', dc, dt, vfoo),
            (ds, 'x86_64', dc, dt, vbar),
        ]
        expected_combinations_inc = [
            # (ds, 'x86', dc, dt, vnone),
            (ds, 'x86', dc, dt, vfoo),
            # (ds, 'x86', dc, dt, vbar),
            # (ds, 'x86_64', dc, dt, vnone),
            # (ds, 'x86_64', dc, dt, vfoo),
            # (ds, 'x86_64', dc, dt, vbar),
        ]
        self.t(args + ["--exclude-builds", rules], expected_items,
               expected_combinations_exc)
        self.t(args + ["--exclude-builds-all", rules], expected_items,
               expected_combinations_exc)
        self.t(args + ["--include-builds", rules], expected_items,
               expected_combinations_inc)
        self.t(args + ["--include-builds-all", rules], expected_items,
               expected_combinations_inc)

    def test04(self):
        rules = "x86-.*foo,x86_64-.*bar"
        args = ["-a", "x86,x86_64", "-v", vspec]
        expected_items = odict([
            ('systems', [ds]),
            ('architectures', ['x86', 'x86_64']),
            ('compilers', [dc]),
            ('build_types', [dt]),
            ('variants', [vnone, vfoo, vbar])
        ])
        expected_combinations_exc_any = [
            (ds, 'x86', dc, dt, vnone),
            # (ds, 'x86', dc, dt, vfoo),
            (ds, 'x86', dc, dt, vbar),
            (ds, 'x86_64', dc, dt, vnone),
            (ds, 'x86_64', dc, dt, vfoo),
            # (ds, 'x86_64', dc, dt, vbar),
        ]
        expected_combinations_exc_all = [
            (ds, 'x86', dc, dt, vnone),
            (ds, 'x86', dc, dt, vfoo),
            (ds, 'x86', dc, dt, vbar),
            (ds, 'x86_64', dc, dt, vnone),
            (ds, 'x86_64', dc, dt, vfoo),
            (ds, 'x86_64', dc, dt, vbar),
        ]
        expected_combinations_inc_any = [
            # (ds, 'x86', dc, dt, vnone),
            (ds, 'x86', dc, dt, vfoo),
            # (ds, 'x86', dc, dt, vbar),
            # (ds, 'x86_64', dc, dt, vnone),
            # (ds, 'x86_64', dc, dt, vfoo),
            (ds, 'x86_64', dc, dt, vbar),
        ]
        expected_combinations_inc_all = [
            # (ds, 'x86', dc, dt, vnone),
            # (ds, 'x86', dc, dt, vfoo),
            # (ds, 'x86', dc, dt, vbar),
            # (ds, 'x86_64', dc, dt, vnone),
            # (ds, 'x86_64', dc, dt, vfoo),
            # (ds, 'x86_64', dc, dt, vbar),
        ]
        self.t(args + ["--exclude-builds", rules], expected_items,
               expected_combinations_exc_any)
        self.t(args + ["--exclude-builds-all", rules], expected_items,
               expected_combinations_exc_all)
        self.t(args + ["--include-builds", rules], expected_items,
               expected_combinations_inc_any)
        self.t(args + ["--include-builds-all", rules], expected_items,
               expected_combinations_inc_all)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    ut.main()
