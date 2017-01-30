#!/usr/bin/env python3

import unittest as ut

from c4.cmany import cmany


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test21VariantSpec(ut.TestCase):

    def c(self, name, var, **ref):
        self.assertEqual(var.name, name)
        for k, refval in ref.items():
            result = getattr(var, k)
            self.assertEqual(result, refval)

    def test01_simple(self):
        v = cmany.Variant("somevariant: -X '-fPIC'")
        v.resolve_refs([v])
        self.c('somevariant', v, cmake_vars=[], defines=[], cflags=[], cxxflags=['-fPIC'])

    def test02_norefs(self):
        vars = ['\'var0: -X "-fPIC" -D VARIANT1,VARIANT_TYPE=1\'',
                '\'var1: -X "-Wall" -D VARIANT2,VARIANT_TYPE=2\'',
                '\'var2: -X nortti,c++14 -D VARIANT3,VARIANT_TYPE=3\'',
        ]
        for w in (vars, ','.join(vars)):
            out = cmany.Variant.create(w)
            self.assertEquals(len(out), 3)
            self.c('var0', out[0], cmake_vars=[], defines=['VARIANT1', 'VARIANT_TYPE=1'], cflags=[], cxxflags=['-fPIC'])
            self.c('var1', out[1], cmake_vars=[], defines=['VARIANT2', 'VARIANT_TYPE=2'], cflags=[], cxxflags=['-Wall'])
            self.c('var2', out[2], cmake_vars=[], defines=['VARIANT3', 'VARIANT_TYPE=3'], cflags=[], cxxflags=['nortti', 'c++14'])

    def test10_refs_beginning(self):
        vars = [
            '\'var0: -X "-fPIC" -D VARIANT1,VARIANT_TYPE=1\'',
            '\'var1: @var0 -X "-Wall" -D VARIANT2,VARIANT_TYPE=2\'',
            '\'var2: @var1 -X nortti,c++14 -D VARIANT3,VARIANT_TYPE=3\'',
        ]
        for w in (vars, ','.join(vars)):
            out = cmany.Variant.create(w)
            self.assertEquals(len(out), 3)
            self.c('var0', out[0], cmake_vars=[], defines=['VARIANT1', 'VARIANT_TYPE=1'], cflags=[], cxxflags=['-fPIC'])
            self.c('var1', out[1], cmake_vars=[], defines=['VARIANT1', 'VARIANT_TYPE=1', 'VARIANT2', 'VARIANT_TYPE=2'], cflags=[], cxxflags=['-fPIC', '-Wall'])
            self.c('var2', out[2], cmake_vars=[], defines=['VARIANT1', 'VARIANT_TYPE=1', 'VARIANT2', 'VARIANT_TYPE=2', 'VARIANT3', 'VARIANT_TYPE=3'], cflags=[], cxxflags=['-fPIC', '-Wall', 'nortti', 'c++14'])

    def test11_refs_middle(self):
        vars = [
            '\'var0: -X "-fPIC" -D VARIANT1,VARIANT_TYPE=1\'',
            '\'var1: -X "-Wall" @var0 -D VARIANT2,VARIANT_TYPE=2\'',
            '\'var2: -X nortti,c++14 @var1 -D VARIANT3,VARIANT_TYPE=3\'',
        ]
        for w in (vars, ','.join(vars)):
            out = cmany.Variant.create(w)
            self.assertEquals(len(out), 3)
            self.c('var0', out[0], cmake_vars=[], defines=['VARIANT1', 'VARIANT_TYPE=1'], cflags=[], cxxflags=['-fPIC'])
            self.c('var1', out[1], cmake_vars=[], defines=['VARIANT1', 'VARIANT_TYPE=1', 'VARIANT2', 'VARIANT_TYPE=2'], cflags=[], cxxflags=['-Wall', '-fPIC'])
            self.c('var2', out[2], cmake_vars=[], defines=['VARIANT1', 'VARIANT_TYPE=1', 'VARIANT2', 'VARIANT_TYPE=2', 'VARIANT3', 'VARIANT_TYPE=3'], cflags=[], cxxflags=['nortti', 'c++14', '-Wall', '-fPIC'])

    def test12_refs_end(self):
        vars = [
            '\'var0: -X "-fPIC" -D VARIANT1,VARIANT_TYPE=1\'',
            '\'var1: -X "-Wall" -D VARIANT2,VARIANT_TYPE=2 @var0\'',
            '\'var2: -X nortti,c++14 -D VARIANT3,VARIANT_TYPE=3 @var1\'',
        ]
        for w in (vars, ','.join(vars)):
            out = cmany.Variant.create(w)
            self.assertEquals(len(out), 3)
            self.c('var0', out[0], cmake_vars=[], defines=['VARIANT1', 'VARIANT_TYPE=1'], cflags=[], cxxflags=['-fPIC'])
            self.c('var1', out[1], cmake_vars=[], defines=['VARIANT2', 'VARIANT_TYPE=2', 'VARIANT1', 'VARIANT_TYPE=1'], cflags=[], cxxflags=['-Wall', '-fPIC'])
            self.c('var2', out[2], cmake_vars=[], defines=['VARIANT3', 'VARIANT_TYPE=3', 'VARIANT2', 'VARIANT_TYPE=2', 'VARIANT1', 'VARIANT_TYPE=1'], cflags=[], cxxflags=['nortti', 'c++14', '-Wall', '-fPIC'])



# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test10Combinations(ut.TestCase):

    pass


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    ut.main()
