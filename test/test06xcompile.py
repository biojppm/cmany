#!/usr/bin/env python3

import unittest as ut
import subtest_fix
import shlex
import shutil
import glob

import os.path as osp

from c4.cmany.main import cmany_main
from c4.cmany import util
from c4.cmany import cmake
from c4.cmany.compiler import Compiler
from c4.cmany.build import Build

mydir = osp.abspath(osp.dirname(__file__))
tc_armhf = osp.join(mydir, "toolchain-arm-linux-gnueabihf.cmake")
assert osp.exists(tc_armhf)
testdirs = [osp.join(mydir, "hello")]


def toolchain_compiler_exists(tc_file):
    comps = cmake.extract_toolchain_compilers(tc_file)
    return osp.exists(comps['CMAKE_CXX_COMPILER'])


def run_with_args(testdir, args_in):
    if isinstance(args_in, str):
        args_in = shlex.split(args_in)
    with util.setcwd(testdir):
        bdir = osp.join('.test', 'xcompile', 'build')
        idir = osp.join('.test', 'xcompile', 'install')
        if osp.exists(bdir):
            shutil.rmtree(bdir)
        if osp.exists(idir):
            shutil.rmtree(idir)
        #
        args = ['--show-args', 'build']
        args += ['--build-dir', bdir, '--install-dir', idir]
        args += args_in
        cmany_main(args)
        #
        with util.setcwd(bdir):
            actual_builds = sorted([str(s) for s in list(glob.glob('*'))])
        return actual_builds


def do_toolchain_builds(toolchain, test, args, expected_builds):
    if not toolchain_compiler_exists(toolchain):
        return
    args = [a.format(toolchain=toolchain) for a in args]
    comps = cmake.extract_toolchain_compilers(toolchain)
    c = Compiler(comps['CMAKE_CXX_COMPILER'])
    expected_builds = [b.format(compiler=Build.sanitize_compiler_name(c.name))
                       for b in expected_builds]
    for t in testdirs:
        with test.subTest(msg=osp.dirname(t), args=args):
            actual_builds = run_with_args(t, args)
            test.assertEqual(actual_builds, expected_builds)


class Test00Arm(ut.TestCase):

    def r(self, args, expected_builds):
        do_toolchain_builds(tc_armhf, self, args, expected_builds)

    def test00(self):
        self.r(["--toolchain", "{toolchain}",
                "-s", "linux",
                "-a", "armv5: -X '-march=armv5'",
                "-a", "armv7: -X '-march=armv7'",
        ], [
            'linux-armv5-{compiler}-Release',
            'linux-armv7-{compiler}-Release',
        ])

    def test01(self):
        self.r(["-s", "linux: --toolchain {toolchain}",
                "-a", "armv5: -X '-march=armv5'",
                "-a", "armv7: -X '-march=armv7'",
        ], [
            'linux-armv5-{compiler}-Release',
            'linux-armv7-{compiler}-Release',
        ])

    def test02(self):
        self.r(["-s", "linux: --toolchain {toolchain}",
                "-a", "armv5: -X '-march=armv5'",
                "-a", "armv7: -X '-march=armv7'",
        ], [
            'linux-armv5-{compiler}-Release',
            'linux-armv7-{compiler}-Release',
        ])

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    ut.main()
