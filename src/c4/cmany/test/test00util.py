#!/usr/bin/env python3

import unittest as ut
import c4.cmany.util as util
import sys
import copy

from collections import OrderedDict as odict


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test00splitspaces(ut.TestCase):

    def t(self, input, output):
        comp = util.splitspaces_quoted(input)
        self.assertEqual(comp, output)

    def _run(self, fn):
        fn('{} {}')
        fn(' {} {}')
        fn(' {} {} ')
        fn('{} {} ')
        fn('{}     {}')
        fn('     {}     {}')
        fn('     {}     {}     ')
        fn('{}     {}     ')

    def test00_spaces_only(self):
        t = lambda fmt: self.t(fmt, [])
        t(' ')
        t('    ')

    def test01_single_letters(self):
        lhs = 'a'
        rhs = 'b'
        self._run(lambda fmt: self.t(fmt.format(lhs, rhs), [lhs, rhs]))

    def test02_multiletters(self):
        lhs = 'a c d e f g h'
        rhs = 'b c d e f g h'
        res = lhs.split(' ') + rhs.split(' ')
        self._run(lambda fmt: self.t(fmt.format(lhs, rhs), res))

    def test03_multiletters_quote_at_begin_not_at_end(self):
        lhs = '"a c d e f g h'
        rhs = 'b c d e f g h'
        res = lhs.split(' ') + rhs.split(' ')
        self._run(lambda fmt: self.t(fmt.format(lhs, rhs), res))

    def test04_multiletters_quote_at_end_not_at_begin(self):
        lhs = 'a c d e f g h'
        rhs = 'b c d e f g h"'
        res = lhs.split(' ') + rhs.split(' ')
        self._run(lambda fmt: self.t(fmt.format(lhs, rhs), res))

    def test10_multiletters_quoted(self):
        lhs = '"a c d e f g h"'
        rhs = '"b c d e f g h"'
        self._run(lambda fmt: self.t(fmt.format(lhs, rhs), [lhs, rhs]))

    def test11_multiletters_quoted_escaped(self):
        lhs = '"a\\" \\"c\\" \\"d\\" \\"e\\" \\"f\\" \\"g\\" \\"h"'
        rhs = '"b\\" \\"c\\" \\"d\\" \\"e\\" \\"f\\" \\"g\\" \\"h"'
        self._run(lambda fmt: self.t(fmt.format(lhs, rhs), [lhs, rhs]))

    def test20_varspecs0(self):
        self.t('-X "-fPIC" -D VARIANT1', ['-X', '"-fPIC"', '-D', 'VARIANT1'])
        self.t('-X "-Wall" -D VARIANT2', ['-X', '"-Wall"', '-D', 'VARIANT2'])
        self.t('-X nortti,c++14 -D VARIANT3', ['-X', 'nortti,c++14', '-D', 'VARIANT3'])

    def test21_varspecs1(self):
        self.t('-X "-fPIC" -D VARIANT1,VARIANT_TYPE=1', ['-X', '"-fPIC"', '-D', 'VARIANT1,VARIANT_TYPE=1'])
        self.t('-X "-Wall" -D VARIANT2,VARIANT_TYPE=2', ['-X', '"-Wall"', '-D', 'VARIANT2,VARIANT_TYPE=2'])
        self.t('-X nortti,c++14 -D VARIANT3,VARIANT_TYPE=3', ['-X', 'nortti,c++14', '-D', 'VARIANT3,VARIANT_TYPE=3'])

    def test22_varspecs2(self):
        self.t('-X "-fPIC" -D VARIANT1,"VARIANT_TYPE=1"', ['-X', '"-fPIC"', '-D', 'VARIANT1,"VARIANT_TYPE=1"'])
        self.t('-X "-Wall" -D VARIANT2,"VARIANT_TYPE=2"', ['-X', '"-Wall"', '-D', 'VARIANT2,"VARIANT_TYPE=2"'])
        self.t('-X nortti,c++14 -D VARIANT3,"VARIANT_TYPE=3"', ['-X', 'nortti,c++14', '-D', 'VARIANT3,"VARIANT_TYPE=3"'])

    def test23_varspecs3(self):
        self.t('-X "-fPIC" -D "VARIANT1,VARIANT_TYPE=1"', ['-X', '"-fPIC"', '-D', '"VARIANT1,VARIANT_TYPE=1"'])
        self.t('-X "-Wall" -D "VARIANT2,VARIANT_TYPE=2"', ['-X', '"-Wall"', '-D', '"VARIANT2,VARIANT_TYPE=2"'])
        self.t('-X nortti,c++14 -D "VARIANT3,VARIANT_TYPE=3"', ['-X', 'nortti,c++14', '-D', '"VARIANT3,VARIANT_TYPE=3"'])


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test01splitesc(ut.TestCase):

    def test(self):
        self.assertEqual(
            util.splitesc('hello\,world,yet\,another', ','),
            ['hello\,world', 'yet\,another'])


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test02nested_merge(ut.TestCase):

    def test00reqs(self):
        import collections
        self.assertTrue(isinstance(dict(), collections.Mapping))
        self.assertTrue(isinstance(collections.OrderedDict(), collections.Mapping))

    def test01do_it(self):
        for fname in ('tc1', 'tc2', 'tc3'):
            fn = getattr(__class__, fname)
            for cls in (dict, odict):
                name, a, b, rab, rba = fn(self, cls)
                with self.subTest(cls=cls.__name__, fn=fname, case=name):
                    vab = util.nested_merge(a, b)
                    self.assertEqual(rab, vab)
                    vab = copy.deepcopy(a)
                    util.nested_merge(vab, b, False)
                    self.assertEqual(rab, vab)
                    #
                    vba = util.nested_merge(b, a)
                    self.assertEqual(rba, vba)
                    vba = copy.deepcopy(b)
                    util.nested_merge(vba, a, False)
                    self.assertEqual(rba, vba)

    def tc1(self, cls):
        return 'empty+empty=empty', cls(), cls(), cls(), cls()
    def tc2(self, cls):
        a = self.someval(cls)
        b = cls()
        return 'flat+empty=flat', a, b, a, a
    def tc3(self, cls):
        a = self.nested(cls, 'c')
        b = cls()
        return 'nested_after+empty=nested_after', a, b, a, a
    def tc3(self, cls):
        a = self.nested(cls, '0')
        b = cls()
        return 'nested_before+empty=nested', a, b, a, a

    def flat(self, cls):
        return self.someval(cls)
    def nested(self, cls, char):
        a = self.someval(cls)
        a[char] = self.someval(cls)
        a[char][char] = self.someval(cls)
        a[char][char][char] = self.someval(cls)
        return a
    def someval(self, cls):
        d = cls()
        d['a'] = 0
        d['b'] = 1
        return d


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test10runsyscmd(ut.TestCase):

    def test00_noargs(self):
        invoke_and_compare(self, [])

    def test01_noargs(self):
        invoke_and_compare(self, ['arg1', 'arg2'])

    def test02_quoted_args(self):
        invoke_and_compare(self, ['"arg1"', '"arg2"'])

    def test03_quoted_args_with_spaces(self):
        invoke_and_compare(self, ['"arg1 and more"', '"arg2 and more"'])


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
echo_args = None
def invoke_and_compare(tester, cmd_args):
    # print("invoke_and_compare: in=", cmd_args)
    cmd = [sys.executable, sys.modules[__name__].__file__, 'echo'] + cmd_args
    out = util.runsyscmd(cmd, echo_cmd=False, capture_output=True).strip()
    # print("invoke_and_compare: out=", out)
    # this doesn't work...:
    # code = "echo_args={}".format(out)
    # ... but this does:
    code = "tmp = " + out + "; setattr(sys.modules[__name__], 'echo_args', tmp)"
    code = code.format(out)
    # print("invoke_and_compare: code=", code)
    exec(code)
    # print("invoke_and_compare: echo_args=", echo_args)
    tester.assertEqual(echo_args, cmd_args)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'echo':
        print(sys.argv[2:])  # for test_invoke()
    else:
        ut.main()
