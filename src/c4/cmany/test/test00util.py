#!/usr/bin/env python3

import unittest as ut
import c4.cmany.util as util
import sys

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
class Test01runsyscmd(ut.TestCase):

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
    cmd = [sys.executable, sys.modules[__name__].__file__, 'echo'] + cmd_args
    out = util.runsyscmd(cmd, echo_cmd=False, capture_output=True)
    # print("invoke_and_compare: out=", out)
    # this doesn't work...:
    # code = "echo_args={}".format(out)
    # ... but this does:
    code = "tmp = out; setattr(sys.modules[__name__], 'echo_args', tmp)"
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
