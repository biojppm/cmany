#!/usr/bin/env python3

import unittest as ut
import subtest_fix
import c4.cmany.util as util
import sys
import copy

from collections import OrderedDict as odict


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test00splitesc(ut.TestCase):
    def test(self):
        self.assertEqual(
            util.splitesc('hello\,world,yet\,another', ','),
            ['hello\,world', 'yet\,another'])


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test01splitesc_quoted(ut.TestCase):

    def t(self, input, expected, split_char=' '):
        with self.subTest(input=input):
            output = util.splitesc_quoted(input, split_char)
            self.assertEqual(output, expected)

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

    def test02_multi_letters(self):
        lhs = 'a c d e f g h'
        rhs = 'b c d e f g h'
        res = lhs.split(' ') + rhs.split(' ')
        self._run(lambda fmt: self.t(fmt.format(lhs, rhs), res))

    def test03_multi_letters_quote_at_begin_not_at_end(self):
        lhs = '"a c d e f g h'
        rhs = 'b c d e f g h'
        res = lhs.split(' ') + rhs.split(' ')
        self._run(lambda fmt: self.t(fmt.format(lhs, rhs), res))

    def test04_multi_letters_quote_at_end_not_at_begin(self):
        lhs = 'a c d e f g h'
        rhs = 'b c d e f g h"'
        res = lhs.split(' ') + rhs.split(' ')
        self._run(lambda fmt: self.t(fmt.format(lhs, rhs), res))


    def test10_multi_letters_quoted(self):
        lhs = '"a c d e f g h"'
        rhs = '"b c d e f g h"'
        self._run(lambda fmt: self.t(fmt.format(lhs, rhs), [lhs, rhs]))
        self.t('"a b c" "d e f" "g h i"', ['"a b c"', '"d e f"', '"g h i"'], ' ')
        self.t('"a,b,c","d,e,f","g,h,i"', ['"a,b,c"', '"d,e,f"', '"g,h,i"'], ',')
        self.t('abc,def,ghi', ['abc', 'def', 'ghi'], ',')
        self.t('abc, def, ghi', ['abc', ' def', ' ghi'], ',')
        self.t('abc ,def ,ghi', ['abc ', 'def ', 'ghi'], ',')
        self.t('abc , def , ghi', ['abc ', ' def ', ' ghi'], ',')

    def test11_multi_letters_quoted_escaped(self):
        lhs = '"a\\" \\"c\\" \\"d\\" \\"e\\" \\"f\\" \\"g\\" \\"h"'
        rhs = '"b\\" \\"c\\" \\"d\\" \\"e\\" \\"f\\" \\"g\\" \\"h"'
        self._run(lambda fmt: self.t(fmt.format(lhs, rhs), [lhs, rhs]))
        self.t('abc\\ def\\ ghi', ['abc\\ def\\ ghi'], ' ')
        self.t('abc\\,def\\,ghi', ['abc\\,def\\,ghi'], ',')
        self.t('abc\\ def\\ ghi abc\\ def\\ ghi', ['abc\\ def\\ ghi', 'abc\\ def\\ ghi'], ' ')
        self.t('abc\\,def\\,ghi,abc\\,def\\,ghi', ['abc\\,def\\,ghi', 'abc\\,def\\,ghi'], ',')


    def test30_varspecs0(self):
        self.t('-X "-fPIC" -D VARIANT1', ['-X', '"-fPIC"', '-D', 'VARIANT1'])
        self.t('-X "-Wall" -D VARIANT2', ['-X', '"-Wall"', '-D', 'VARIANT2'])
        self.t('-X nortti,c++14 -D VARIANT3', ['-X', 'nortti,c++14', '-D', 'VARIANT3'])

    def test31_varspecs1(self):
        self.t('-X "-fPIC" -D VARIANT1,VARIANT_TYPE=1', ['-X', '"-fPIC"', '-D', 'VARIANT1,VARIANT_TYPE=1'])
        self.t('-X "-Wall" -D VARIANT2,VARIANT_TYPE=2', ['-X', '"-Wall"', '-D', 'VARIANT2,VARIANT_TYPE=2'])
        self.t('-X nortti,c++14 -D VARIANT3,VARIANT_TYPE=3', ['-X', 'nortti,c++14', '-D', 'VARIANT3,VARIANT_TYPE=3'])

    def test32_varspecs2(self):
        self.t('-X "-fPIC" -D VARIANT1,"VARIANT_TYPE=1"', ['-X', '"-fPIC"', '-D', 'VARIANT1,"VARIANT_TYPE=1"'])
        self.t('-X "-Wall" -D VARIANT2,"VARIANT_TYPE=2"', ['-X', '"-Wall"', '-D', 'VARIANT2,"VARIANT_TYPE=2"'])
        self.t('-X nortti,c++14 -D VARIANT3,"VARIANT_TYPE=3"', ['-X', 'nortti,c++14', '-D', 'VARIANT3,"VARIANT_TYPE=3"'])

    def test33_varspecs3(self):
        self.t('-X "-fPIC" -D "VARIANT1,VARIANT_TYPE=1"', ['-X', '"-fPIC"', '-D', '"VARIANT1,VARIANT_TYPE=1"'])
        self.t('-X "-Wall" -D "VARIANT2,VARIANT_TYPE=2"', ['-X', '"-Wall"', '-D', '"VARIANT2,VARIANT_TYPE=2"'])
        self.t('-X nortti,c++14 -D "VARIANT3,VARIANT_TYPE=3"', ['-X', 'nortti,c++14', '-D', '"VARIANT3,VARIANT_TYPE=3"'])


    def test40_multiple_varspecs0(self):
        var0 = '"var0: -X \\"-g\\",\\"-g3\\",\\"-Wall\\" -D VAR0,DBG"'
        var1 = '"var1: -X \\"-O1\\",\\"-ffast-math\\" -D VAR1,OPTM"'
        self.t('{},{}'.format(var0, var1), [var0, var1], ',')


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test02is_quoted(ut.TestCase):

    def test00simple(self):
        t = lambda s, expected: self.assertEqual(util.is_quoted(s), expected, msg=s)
        t('aasdasdasdasdasd', False)
        t('aasdasda""dasdasd', False)
        t('aasdasda''dasdasd', False)
        t('"aasdasdasdasdasd"', True)
        t("'aasdasdasdasdasd'", True)
        t('"aasdasda,sdasdasd"', True)
        t("'aasdasda,sdasdasd'", True)
        t('"aasdasda","sdasdasd"', False)
        t("'aasdasda','sdasdasd'", False)
        t('"aasdasda","sdasdasd","sdasdasd","sdasdasd"', False)
        t("'aasdasda','sdasdasd','aasdasda','sdasdasd'", False)
        t("'aasdasda',sdasdasd,aasdasda,'sdasdasd'", False)

    def test01nested(self):
        t = lambda s, expected: self.assertEqual(util.is_quoted(s), expected, msg=s)
        t("\'aasdasda,sdasdasd\'", True)
        t("\\'aasdasda,sdasdasd\\'", False)
        t('\'aasdasda,sdasdasd\'', True)
        t('\\\'aasdasda,sdasdasd\\\'', False)
        t("'aasdasda',\"sdasdasd\",'aasdasda',\"sdasdasd\"", False)
        t("'aasdasda',\'sdasdasd\'", False)
        #
        t("\'aasdasda,sdasdasd\'", True)
        t("\\'aasdasda,sdasdasd\\'", False)
        #
        t("'\'aasdasda\',\'sdasdasd\''", False)
        t("'\\'aasdasda\\',\\'sdasdasd\\''", True)

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test04has_interior_quotes(ut.TestCase):

    def test(self):
        t = lambda s, expected: self.assertEqual(util.has_interior_quotes(s), expected, msg=s)
        t('aaaaaa,bbbbbbb', False)
        t('"aaaaaa,bbbbbb"', False)
        t('aaaaaa,"bbbbbb"', True)
        t('"aaaaaa",bbbbbb', True)
        t('aaaaaa",bbbbbb', True)
        t('aaaaaa,"bbbbbb', True)
        t("none,'xdebug: --cxxflags g3'", True)
        t('none,"xdebug: --cxxflags g3"', True)
        t("none,\"xdebug: --cxxflags g3\"", True)
        t('none,\'xdebug: --cxxflags g3\'', True)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test05intersperse(ut.TestCase):

    def test_left(self):
        def t(li):
            expected = []
            for l in li:
                expected += ['delim', l]
            output = list(util.intersperse_l('delim', li))
            with self.subTest(input=li, version='left'):
                self.assertEqual(output, expected)
        t([0, 1, 2])
        t([2, 1, 0])


    def test_right(self):
        def t(li):
            expected = []
            for l in li:
                expected += [l, 'delim']
            output = list(util.intersperse_r('delim', li))
            with self.subTest(input=li, version='right'):
                self.assertEqual(output, expected)

        t([0, 1, 2])
        t([2, 1, 0])


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test09nested_merge(ut.TestCase):

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
    def tc4(self, cls):
        a = self.nested(cls, '0')
        b = cls()
        return 'nested_before+empty=nested_before', a, b, a, a

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
