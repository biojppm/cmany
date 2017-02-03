#!/usr/bin/env python3

import unittest as ut
import argparse

from c4.cmany import cmanys as cmany, util, args as c4args


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test00VariantSpec(ut.TestCase):

    def c(self, name, var, **ref):
        self.assertEqual(var.name, name)
        for k, refval in ref.items():
            result = getattr(var, k)
            self.assertEqual(result, refval)

    def test01_simple(self):
        v = cmany.Variant.create("somevariant: -X '-fPIC'")
        v = v[0]
        self.c('somevariant', v, cmake_vars=[], defines=[], cflags=[], cxxflags=['-fPIC'])

    def test02_norefs(self):
        vars = ['\'var0: -X "-fPIC" -D VAR1,VAR_TYPE=1\'',
                '\'var1: -X "-Wall" -D VAR2,VAR_TYPE=2\'',
                '\'var2: -X nortti,c++14 -D VAR3,VAR_TYPE=3\'',
        ]
        for w in (vars, ','.join(vars)):
            out = cmany.Variant.create(w)
            self.assertEquals(len(out), 3)
            self.c('var0', out[0], cmake_vars=[], defines=['VAR1', 'VAR_TYPE=1'], cflags=[], cxxflags=['-fPIC'])
            self.c('var1', out[1], cmake_vars=[], defines=['VAR2', 'VAR_TYPE=2'], cflags=[], cxxflags=['-Wall'])
            self.c('var2', out[2], cmake_vars=[], defines=['VAR3', 'VAR_TYPE=3'], cflags=[], cxxflags=['nortti', 'c++14'])

    def test10_refs_beginning(self):
        vars = [
            '\'var0: -X "-fPIC" -D VAR1,VAR_TYPE=1\'',
            '\'var1: @var0 -X "-Wall" -D VAR2,VAR_TYPE=2\'',
            '\'var2: @var1 -X nortti,c++14 -D VAR3,VAR_TYPE=3\'',
        ]
        for w in (vars, ','.join(vars)):
            out = cmany.Variant.create(w)
            self.assertEquals(len(out), 3)
            self.c('var0', out[0], cmake_vars=[], defines=['VAR1', 'VAR_TYPE=1'], cflags=[], cxxflags=['-fPIC'])
            self.c('var1', out[1], cmake_vars=[], defines=['VAR1', 'VAR_TYPE=1', 'VAR2', 'VAR_TYPE=2'], cflags=[], cxxflags=['-fPIC', '-Wall'])
            self.c('var2', out[2], cmake_vars=[], defines=['VAR1', 'VAR_TYPE=1', 'VAR2', 'VAR_TYPE=2', 'VAR3', 'VAR_TYPE=3'], cflags=[], cxxflags=['-fPIC', '-Wall', 'nortti', 'c++14'])

    def test11_refs_middle(self):
        vars = [
            '\'var0: -X "-fPIC" -D VAR1,VAR_TYPE=1\'',
            '\'var1: -X "-Wall" @var0 -D VAR2,VAR_TYPE=2\'',
            '\'var2: -X nortti,c++14 @var1 -D VAR3,VAR_TYPE=3\'',
        ]
        for w in (vars, ','.join(vars)):
            out = cmany.Variant.create(w)
            self.assertEquals(len(out), 3)
            self.c('var0', out[0], cmake_vars=[], defines=['VAR1', 'VAR_TYPE=1'], cflags=[], cxxflags=['-fPIC'])
            self.c('var1', out[1], cmake_vars=[], defines=['VAR1', 'VAR_TYPE=1', 'VAR2', 'VAR_TYPE=2'], cflags=[], cxxflags=['-Wall', '-fPIC'])
            self.c('var2', out[2], cmake_vars=[], defines=['VAR1', 'VAR_TYPE=1', 'VAR2', 'VAR_TYPE=2', 'VAR3', 'VAR_TYPE=3'], cflags=[], cxxflags=['nortti', 'c++14', '-Wall', '-fPIC'])

    def test12_refs_end(self):
        vars = [
            '\'var0: -X "-fPIC" -D VAR1,VAR_TYPE=1\'',
            '\'var1: -X "-Wall" -D VAR2,VAR_TYPE=2 @var0\'',
            '\'var2: -X nortti,c++14 -D VAR3,VAR_TYPE=3 @var1\'',
        ]
        for w in (vars, ','.join(vars)):
            out = cmany.Variant.create(w)
            self.assertEquals(len(out), 3)
            self.c('var0', out[0], cmake_vars=[], defines=['VAR1', 'VAR_TYPE=1'], cflags=[], cxxflags=['-fPIC'])
            self.c('var1', out[1], cmake_vars=[], defines=['VAR2', 'VAR_TYPE=2', 'VAR1', 'VAR_TYPE=1'], cflags=[], cxxflags=['-Wall', '-fPIC'])
            self.c('var2', out[2], cmake_vars=[], defines=['VAR3', 'VAR_TYPE=3', 'VAR2', 'VAR_TYPE=2', 'VAR1', 'VAR_TYPE=1'], cflags=[], cxxflags=['nortti', 'c++14', '-Wall', '-fPIC'])

    def test22_consecutive_refs_only(self):
        vars = [
            '\'var0: -X "-fPIC" -D VAR1,VAR_TYPE=1\'',
            '\'var1: -X "-Wall" -D VAR2,VAR_TYPE=2\'',
            '\'var2: -X "-g3" -D VAR3,VAR_TYPE=3\'',
            '\'var3: @var0 @var1\'',
            '\'var4: @var0 @var1 @var2\'',
        ]
        for w in (vars, ','.join(vars)):
            out = cmany.Variant.create(w)
            self.assertEquals(len(out), 5)
            self.c('var0', out[0], cmake_vars=[], defines=['VAR1', 'VAR_TYPE=1'], cflags=[], cxxflags=['-fPIC'])
            self.c('var1', out[1], cmake_vars=[], defines=['VAR2', 'VAR_TYPE=2'], cflags=[], cxxflags=['-Wall'])
            self.c('var2', out[2], cmake_vars=[], defines=['VAR3', 'VAR_TYPE=3'], cflags=[], cxxflags=['-g3'])
            self.c('var3', out[3], cmake_vars=[], defines=['VAR1', 'VAR_TYPE=1', 'VAR2', 'VAR_TYPE=2'], cflags=[], cxxflags=['-fPIC', '-Wall'])
            self.c('var4', out[4], cmake_vars=[], defines=['VAR1', 'VAR_TYPE=1', 'VAR2', 'VAR_TYPE=2', 'VAR3', 'VAR_TYPE=3'], cflags=[], cxxflags=['-fPIC', '-Wall', '-g3'])


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test10AsArguments(ut.TestCase):

    def t(self, input, expected):
        parser = argparse.ArgumentParser()
        c4args.add_select(parser)
        args = parser.parse_args(input)
        with self.subTest(input=input, desc='argument parsing'):
            self.assertEqual(args.variants, expected, msg=input)

    def tp(self, input, which_var, expected_name, **expected_props):
        parser = argparse.ArgumentParser()
        c4args.add_select(parser)
        args = parser.parse_args(input)
        vars = cmany.Variant.create(args.variants)
        self.assertTrue(which_var < len(vars))
        var = vars[which_var]
        self.assertEqual(var.name, expected_name)
        for k, refval in expected_props.items():
            result = getattr(var, k)
            with self.subTest(input=input, which_var=which_var, desc='variant properties', prop=k):
                self.assertEqual(result, refval, msg='property: ' + k)

    def r(self, input, expected):
        isl = list(util.intersperse_l("-v", input))
        self.t(isl, expected)
        isl = list(util.intersperse_l("--variant", input))
        self.t(isl, expected)

    def rp(self, input, which_var, expected_name, **expected_props):
        isl = list(util.intersperse_l("-v", input))
        self.tp(isl, which_var, expected_name, **expected_props)
        isl = list(util.intersperse_l("--variant", input))
        self.tp(isl, which_var, expected_name, **expected_props)

    def test00(self):
        self.t([], [])
        self.t(["-v", "none"], ['none'])

    def test01(self):
        self.t(["-v", "none", "-v", 'xdebug: --cxxflags g3'], ['none', 'xdebug: --cxxflags g3'])
        self.t(["-v", "none,'xdebug: --cxxflags g3'"], ['none', 'xdebug: --cxxflags g3'])

    def test02(self):
        vars = [
            "none",
            "just_no_rtti: --cxxflags no_rtti",
            "fast: @just_no_rtti --cxxflags no_exceptions,no_bufsec,no_iterator_debug,fast_math"
        ]
        #
        self.r(vars, vars)
        # join first two
        j = '{},"{}"'.format(vars[0], vars[1])
        self.r([j, vars[2]], vars)
        # join second two
        j = '"{}","{}"'.format(vars[1], vars[2])
        self.r([vars[0], j], vars)
        # join all
        j = '"{}","{}","{}"'.format(vars[0], vars[1], vars[2])
        self.r([j], vars)

    def test03(self):
        vars = [
            "none",
            "dbg3: -X '-g3' -D DBG3",
            "wall: -X '-Wall' -D WALL",
            "dbg3_wall: @dbg3 @wall"
        ]
        def comp(input):
            with self.subTest(input=input):
                self.r(input, vars)
                self.rp(input, 0, 'none')
                self.rp(input, 1, 'dbg3', cxxflags=['-g3'], defines=['DBG3'])
                self.rp(input, 2, 'wall', cxxflags=['-Wall'], defines=['WALL'])
                self.rp(input, 3, 'dbg3_wall', cxxflags=['-g3','-Wall'], defines=['DBG3','WALL'])
        # all separate
        comp(vars)
        # join first two
        j = '{},"{}"'.format(vars[0], vars[1])
        comp([j, vars[2], vars[3]])
        # join second two
        j = '"{}","{}"'.format(vars[1], vars[2])
        comp([vars[0], j, vars[3]])
        # join third two
        j = '"{}","{}"'.format(vars[2], vars[3])
        comp([vars[0], vars[1], j])
        # join first three
        j = '"{}","{}","{}"'.format(vars[0], vars[1], vars[2])
        comp([j, vars[3]])
        # join all
        j = '"{}","{}","{}","{}"'.format(vars[0], vars[1], vars[2], vars[3])
        comp([j])

    def test04(self):
        s = ['-v', "none,\"just_no_rtti: --cxxflags no_rtti\"",
             '-v', "fast: @just_no_rtti --cxxflags no_exceptions,no_bufsec,no_iterator_debug,fast_math"]
        self.tp(s, 0, 'none')
        self.tp(s, 1, 'just_no_rtti')
        self.tp(s, 2, 'fast')


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test11AsUnquotedArguments(ut.TestCase):
    """the shell removes quotes from the arguments, so variant parsing
    must be able to deal with unquoted specs"""

    def t(self, input, expected):
        variants = cmany.Variant.parse_specs(input)
        with self.subTest(input=input):
            self.assertEqual(variants, expected, msg=input)

    def test00(self):
        var0 = 'none'
        var1 = 'just_no_rtti: --cxxflags no_rtti'
        self.t(var0 + ',' + var1, [var0, var1])

    def test01(self):
        var0 = 'none'
        var1 = 'just_no_rtti: --cxxflags no_rtti'
        var2 = 'fast: @just_no_rtti --cxxflags no_exceptions,no_bufsec,no_iterator_debug,fast_math'
        self.t(var0 + ',' + var1 + ',' + var2, [var0, var1, var2])


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    ut.main()
