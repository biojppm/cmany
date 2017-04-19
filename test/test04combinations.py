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


def do_combination_t(test, input, expected_items, expected_combinations):
    assert isinstance(expected_items, odict)

    _parser = argparse.ArgumentParser()
    c4args.add_select(_parser)
    c4args.add_bundle_flags(_parser)

    args = _parser.parse_args(input)
    # util.logcmd(input, "\n", args)

    for i in ('systems', 'architectures', 'compilers', 'build_types', 'variants'):
        expected = expected_items[i]
        expected = [e.split(':')[0] for e in expected]
        actual = getattr(args, i)
        actual = [a.split(':')[0] for a in actual]
        # print(i, "actual=", actual)
        # print(i, "expected=", expected)
        # with test.subTest(msg="expected count of "+i, input=input):
        #    test.assertEqual(len(actual), len(expected))
        with test.subTest(msg="expected list of "+i, input=input):
            test.assertEqual(actual, expected)

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

    # print("\n")
    # for i, (e, a) in enumerate(zip(expected_combinations, actual_combinations)):
    #     print("expected[{}]".format(i), e, "actual[{}]".format(i), a)
    with test.subTest(msg="expected count of combinations", input=input):
        test.assertEqual(len(expected_combinations), len(actual_combinations))
    for exp, act in zip(expected_combinations, actual_combinations):
        #print("exp x act:", exp, act)
        with test.subTest(msg="combination architecture", input=input):
            test.assertEqual(act[0].name, exp[0].name)
        with test.subTest(msg="combination system", input=input):
            test.assertEqual(act[1].name, exp[1].name)
        with test.subTest(msg="combination compiler", input=input):
            test.assertEqual(act[2].name, exp[2].name)
        with test.subTest(msg="combination build type", input=input):
            test.assertEqual(act[3].name, exp[3].name)
        with test.subTest(msg="combination variant", input=input):
            test.assertEqual(act[4].name, exp[4].name)


class CombinationTestCase(ut.TestCase):

    def t(self, input, expected_items, expected_combinations):
        do_combination_t(self, input, expected_items, expected_combinations)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test00BaseLine(CombinationTestCase):

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

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test01AtCommandLevel(CombinationTestCase):

    def test01(self):
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

    def test02(self):
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

    def test03(self):
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

    def test10exc_x86(self):
        args = ["-a", "x86,x86_64", "-v", vspec]
        expected_items = odict([
            ('systems', [ds]),
            ('architectures', ['x86', 'x86_64']),
            ('compilers', [dc]),
            ('build_types', [dt]),
            ('variants', [vnone, vfoo, vbar])
        ])
        expected_combinations_exc = [
            # (ds, 'x86', dc, dt, vnone),
            # (ds, 'x86', dc, dt, vfoo),
            # (ds, 'x86', dc, dt, vbar),
            (ds, 'x86_64', dc, dt, vnone),
            (ds, 'x86_64', dc, dt, vfoo),
            (ds, 'x86_64', dc, dt, vbar),
        ]
        expected_combinations_inc = [
            (ds, 'x86', dc, dt, vnone),
            (ds, 'x86', dc, dt, vfoo),
            (ds, 'x86', dc, dt, vbar),
            # (ds, 'x86_64', dc, dt, vnone),
            # (ds, 'x86_64', dc, dt, vfoo),
            # (ds, 'x86_64', dc, dt, vbar),
        ]
        self.t(args + ["-xa", 'x86'], expected_items,
               expected_combinations_exc)
        self.t(args + ["--exclude-architectures", 'x86'], expected_items,
               expected_combinations_exc)
        self.t(args + ["-ia", 'x86'], expected_items,
               expected_combinations_inc)
        self.t(args + ["--include-architectures", 'x86'], expected_items,
               expected_combinations_inc)

    def test11exc_x86_64(self):
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
            # (ds, 'x86_64', dc, dt, vnone),
            # (ds, 'x86_64', dc, dt, vfoo),
            # (ds, 'x86_64', dc, dt, vbar),
        ]
        expected_combinations_inc = [
            # (ds, 'x86', dc, dt, vnone),
            # (ds, 'x86', dc, dt, vfoo),
            # (ds, 'x86', dc, dt, vbar),
            (ds, 'x86_64', dc, dt, vnone),
            (ds, 'x86_64', dc, dt, vfoo),
            (ds, 'x86_64', dc, dt, vbar),
        ]
        self.t(args + ["-xa", 'x86_64'], expected_items,
               expected_combinations_exc)
        self.t(args + ["--exclude-architectures", 'x86_64'], expected_items,
               expected_combinations_exc)
        self.t(args + ["-ia", 'x86_64'], expected_items,
               expected_combinations_inc)
        self.t(args + ["--include-architectures", 'x86_64'], expected_items,
               expected_combinations_inc)

    def test12exc_x86_and_x86_64(self):
        args = ["-a", "x86,x86_64", "-v", vspec]
        expected_items = odict([
            ('systems', [ds]),
            ('architectures', ['x86', 'x86_64']),
            ('compilers', [dc]),
            ('build_types', [dt]),
            ('variants', [vnone, vfoo, vbar])
        ])
        expected_combinations_exc = [
            # (ds, 'x86', dc, dt, vnone),
            # (ds, 'x86', dc, dt, vfoo),
            # (ds, 'x86', dc, dt, vbar),
            # (ds, 'x86_64', dc, dt, vnone),
            # (ds, 'x86_64', dc, dt, vfoo),
            # (ds, 'x86_64', dc, dt, vbar),
        ]
        expected_combinations_inc = [
            (ds, 'x86', dc, dt, vnone),
            (ds, 'x86', dc, dt, vfoo),
            (ds, 'x86', dc, dt, vbar),
            (ds, 'x86_64', dc, dt, vnone),
            (ds, 'x86_64', dc, dt, vfoo),
            (ds, 'x86_64', dc, dt, vbar),
        ]
        self.t(args + ["-xa", 'x86_64,x86'], expected_items,
               expected_combinations_exc)
        self.t(args + ["--exclude-architectures", 'x86_64,x86'], expected_items,
               expected_combinations_exc)
        self.t(args + ["-ia", 'x86_64,x86'], expected_items,
               expected_combinations_inc)
        self.t(args + ["--include-architectures", 'x86_64,x86'], expected_items,
               expected_combinations_inc)

    def test13exc_other(self):
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
            (ds, 'x86_64', dc, dt, vfoo),
            (ds, 'x86_64', dc, dt, vbar),
        ]
        expected_combinations_inc = [
            # (ds, 'x86', dc, dt, vnone),
            # (ds, 'x86', dc, dt, vfoo),
            # (ds, 'x86', dc, dt, vbar),
            # (ds, 'x86_64', dc, dt, vnone),
            # (ds, 'x86_64', dc, dt, vfoo),
            # (ds, 'x86_64', dc, dt, vbar),
        ]
        self.t(args + ["-xa", 'other'], expected_items,
               expected_combinations_exc)
        self.t(args + ["--exclude-architectures", 'other'], expected_items,
               expected_combinations_exc)
        self.t(args + ["-ia", 'other'], expected_items,
               expected_combinations_inc)
        self.t(args + ["--include-architectures", 'other'], expected_items,
               expected_combinations_inc)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test02AtBuildItemLevel(CombinationTestCase):

    def test01(self):
        args_exc = ["-a", "'x86: -xv foo',x86_64", "-t", "Debug,Release", "-v", vspec]
        args_inc = ["-a", "'x86: -iv foo',x86_64", "-t", "Debug,Release", "-v", vspec]
        expected_items = odict([
            ('systems', [ds]),
            ('architectures', ['x86', 'x86_64']),
            ('compilers', [dc]),
            ('build_types', ['Debug', 'Release']),
            ('variants', [vnone, vfoo, vbar])
        ])
        expected_combinations_exc = [
            (ds, 'x86', dc, 'Debug', vnone),
            # (ds, 'x86', dc, 'Debug', vfoo),
            (ds, 'x86', dc, 'Debug', vbar),
            (ds, 'x86', dc, 'Release', vnone),
            # (ds, 'x86', dc, 'Release', vfoo),
            (ds, 'x86', dc, 'Release', vbar),
            (ds, 'x86_64', dc, 'Debug', vnone),
            (ds, 'x86_64', dc, 'Debug', vfoo),
            (ds, 'x86_64', dc, 'Debug', vbar),
            (ds, 'x86_64', dc, 'Release', vnone),
            (ds, 'x86_64', dc, 'Release', vfoo),
            (ds, 'x86_64', dc, 'Release', vbar),
        ]
        expected_combinations_inc = [
            #(ds, 'x86', dc, 'Debug', vnone),
            (ds, 'x86', dc, 'Debug', vfoo),
            #(ds, 'x86', dc, 'Debug', vbar),
            #(ds, 'x86', dc, 'Release', vnone),
            (ds, 'x86', dc, 'Release', vfoo),
            #(ds, 'x86', dc, 'Release', vbar),
            (ds, 'x86_64', dc, 'Debug', vnone),
            (ds, 'x86_64', dc, 'Debug', vfoo),
            (ds, 'x86_64', dc, 'Debug', vbar),
            (ds, 'x86_64', dc, 'Release', vnone),
            (ds, 'x86_64', dc, 'Release', vfoo),
            (ds, 'x86_64', dc, 'Release', vbar),
        ]
        self.t(args_exc, expected_items, expected_combinations_exc)
        self.t(args_inc, expected_items, expected_combinations_inc)

    def test02(self):
        args_exc = ["-a", "'x86: -xt Debug',x86_64", "-t", "Debug,Release", "-v", vspec]
        args_inc = ["-a", "'x86: -it Debug',x86_64", "-t", "Debug,Release", "-v", vspec]
        expected_items = odict([
            ('systems', [ds]),
            ('architectures', ['x86', 'x86_64']),
            ('compilers', [dc]),
            ('build_types', ['Debug', 'Release']),
            ('variants', [vnone, vfoo, vbar])
        ])
        expected_combinations_exc = [
            # (ds, 'x86', dc, 'Debug', vnone),
            # (ds, 'x86', dc, 'Debug', vfoo),
            # (ds, 'x86', dc, 'Debug', vbar),
            (ds, 'x86', dc, 'Release', vnone),
            (ds, 'x86', dc, 'Release', vfoo),
            (ds, 'x86', dc, 'Release', vbar),
            (ds, 'x86_64', dc, 'Debug', vnone),
            (ds, 'x86_64', dc, 'Debug', vfoo),
            (ds, 'x86_64', dc, 'Debug', vbar),
            (ds, 'x86_64', dc, 'Release', vnone),
            (ds, 'x86_64', dc, 'Release', vfoo),
            (ds, 'x86_64', dc, 'Release', vbar),
        ]
        expected_combinations_inc = [
            (ds, 'x86', dc, 'Debug', vnone),
            (ds, 'x86', dc, 'Debug', vfoo),
            (ds, 'x86', dc, 'Debug', vbar),
            #(ds, 'x86', dc, 'Release', vnone),
            #(ds, 'x86', dc, 'Release', vfoo),
            #(ds, 'x86', dc, 'Release', vbar),
            (ds, 'x86_64', dc, 'Debug', vnone),
            (ds, 'x86_64', dc, 'Debug', vfoo),
            (ds, 'x86_64', dc, 'Debug', vbar),
            (ds, 'x86_64', dc, 'Release', vnone),
            (ds, 'x86_64', dc, 'Release', vfoo),
            (ds, 'x86_64', dc, 'Release', vbar),
        ]
        self.t(args_exc, expected_items, expected_combinations_exc)
        self.t(args_inc, expected_items, expected_combinations_inc)

    def test03(self):
        args_exc = ["-a", "'x86: -xt Debug -xv foo',x86_64", "-t", "Debug,Release", "-v", vspec]
        args_inc = ["-a", "'x86: -it Debug -iv foo',x86_64", "-t", "Debug,Release", "-v", vspec]
        expected_items = odict([
            ('systems', [ds]),
            ('architectures', ['x86', 'x86_64']),
            ('compilers', [dc]),
            ('build_types', ['Debug', 'Release']),
            ('variants', [vnone, vfoo, vbar])
        ])
        expected_combinations_exc = [
            # (ds, 'x86', dc, 'Debug', vnone),
            # (ds, 'x86', dc, 'Debug', vfoo),
            # (ds, 'x86', dc, 'Debug', vbar),
            (ds, 'x86', dc, 'Release', vnone),
            #(ds, 'x86', dc, 'Release', vfoo),
            (ds, 'x86', dc, 'Release', vbar),
            (ds, 'x86_64', dc, 'Debug', vnone),
            (ds, 'x86_64', dc, 'Debug', vfoo),
            (ds, 'x86_64', dc, 'Debug', vbar),
            (ds, 'x86_64', dc, 'Release', vnone),
            (ds, 'x86_64', dc, 'Release', vfoo),
            (ds, 'x86_64', dc, 'Release', vbar),
        ]
        expected_combinations_inc = [
            #(ds, 'x86', dc, 'Debug', vnone),
            (ds, 'x86', dc, 'Debug', vfoo),
            #(ds, 'x86', dc, 'Debug', vbar),
            #(ds, 'x86', dc, 'Release', vnone),
            #(ds, 'x86', dc, 'Release', vfoo),
            #(ds, 'x86', dc, 'Release', vbar),
            (ds, 'x86_64', dc, 'Debug', vnone),
            (ds, 'x86_64', dc, 'Debug', vfoo),
            (ds, 'x86_64', dc, 'Debug', vbar),
            (ds, 'x86_64', dc, 'Release', vnone),
            (ds, 'x86_64', dc, 'Release', vfoo),
            (ds, 'x86_64', dc, 'Release', vbar),
        ]
        self.t(args_exc, expected_items, expected_combinations_exc)
        self.t(args_inc, expected_items, expected_combinations_inc)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    ut.main()
