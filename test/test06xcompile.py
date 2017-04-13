#!/usr/bin/env python3

import unittest as ut
import subtest_fix
import shlex

import os.path as osp

from c4.cmany.main import cmany_main
from c4.cmany import util

mydir = osp.abspath(osp.dirname(__file__))
tc_armhf = osp.join(mydir, "toolchain-arm-linux-gnueabihf.cmake")
assert osp.exists(tc_armhf)
testdirs = [osp.join(mydir, "hello")]

class Test00Arm(ut.TestCase):

    def t(self, testdir, args):
        if isinstance(args, str):
            args = shlex.split(args)
        with util.setcwd(testdir):
            cmany_main(args)

    def test00(self):
        args = ["--show-args", "b",
                "-s", "linux: --toolchain {tc}".format(tc=tc_armhf),
                "-a", "armv5: -X '-march=armv5'",
                "-a", "armv7: -X '-march=armv7'",]
        for t in testdirs:
            with self.subTest(msg=osp.dirname(t), args=args):
                self.t(t, args)
