#!/usr/bin/env python3

import unittest as ut
import os
import sys
import glob

import c4.cmany.util as util
import c4.cmany.main as main
import c4.cmany.cmany as cmany
import c4.cmany.cmake_sysinfo as cmake

maincmd = [sys.executable, '-m', 'c4.cmany.main']

projdir = os.path.dirname(__file__)
compiler_set = os.environ.get('CMANY_TEST_COMPILERS', None)
build_types = os.environ.get('CMANY_TEST_BUILDTYPES', 'Debug,Release')
test_projs = os.environ.get('CMANY_TEST_PROJS', 'hello')

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class CMakeTestProj:

    def __init__(self, proj):
        self.proj = proj
        self.root = os.path.join(projdir, proj)

    def _run(self, args):
        with util.setcwd(self.root):
            args = maincmd + args
            util.runsyscmd(args)

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# prepare inputs

test_projs = util.splitesc(test_projs, ',')
projs = [CMakeTestProj(p) for p in test_projs]

if compiler_set is None:
    compiler_set = [cmany.Compiler.default()]
else:
    compiler_set = [cmany.Compiler(c) for c in util.splitesc(compiler_set, ',')]

build_types = [cmany.BuildType(b) for b in util.splitesc(build_types, ',')]


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
def run_projs(testobj, args, check_fn=None):
    numbuilds = len(compiler_set) * len(build_types)
    for p in projs:

        # run with default parameters
        bd = '.test/0--default--build'
        id = '.test/0--default--install'
        p._run(args + ['--build-dir', bd,
                       '--install-dir', id])
        if check_fn:
            tb = TestBuild(proj=p, buildroot=bd, installroot=id,
                           compiler=cmany.Compiler.default(),
                           buildtype=cmany.BuildType.default(),
                           numbuilds=1)
            check_fn(tb)

        if numbuilds == 1:
            continue

        # run all combinations at once
        bd = '.test/1--comps{}--types{}--build'.format(len(compiler_set), len(build_types))
        id = '.test/1--comps{}--types{}--install'.format(len(compiler_set), len(build_types))
        p._run(args + ['--build-dir', bd,
                       '--install-dir', id,
                       '-c', ','.join([c.name if c.is_msvc else c.path for c in compiler_set]),
                       '-t', ','.join([str(b) for b in build_types])])
        if check_fn:
            for c in compiler_set:
                for t in build_types:
                    tb = TestBuild(proj=p, buildroot=bd, installroot=id,
                                   compiler=c, buildtype=t,
                                   numbuilds=numbuilds)
                    check_fn(tb)

        # run combinations individually
        for c in compiler_set:
            for t in build_types:
                bd = '.test/2--{}--{}--build'.format(c, t)
                id = '.test/2--{}--{}--install'.format(c, t)
                p._run(args + ['--build-dir', bd,
                         '--install-dir', id,
                         '-c', c.name if c.is_msvc else c.path,
                         '-t', str(t)])
                if check_fn:
                    tb = TestBuild(proj=p, buildroot=bd, installroot=id,
                                   compiler=c, buildtype=t,
                                   numbuilds=1)
                    check_fn(tb)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class TestBuild:

    def __init__(self, proj, buildroot, installroot, compiler, buildtype, numbuilds):
        self.proj = proj
        self.buildroot = buildroot
        self.installroot = installroot
        self.compiler = compiler
        self.buildtype = buildtype
        self.numbuilds = numbuilds
        self.flags = cmany.CompileOptions()
        self.build_obj = cmany.Build(proj_root=self.proj.root,
                                     build_root=os.path.join(self.proj.root, self.buildroot),
                                     install_root=os.path.join(self.proj.root, self.installroot),
                                     system=cmany.System.default(),
                                     arch=cmany.Architecture.default(),
                                     buildtype=buildtype,
                                     compiler=compiler,
                                     variant="",
                                     flags=self.flags,
                                     num_jobs=cmany.cpu_count()
                                     )

    def checkc(self, tester):
        tester.assertEqual(self.nsiblings(self.buildroot), self.numbuilds)
        buildtype = cmake.getcachevar(self.build_obj.builddir, 'CMAKE_BUILD_TYPE')
        tester.assertEqual(buildtype, str(self.buildtype))

    def checkb(self, tester):
        self.checkc(tester)

    def checki(self, tester):
        tester.assertEqual(self.nsiblings(self.installroot), self.numbuilds)

    def nsiblings(self, dir):
        res = os.path.join(self.proj.root, dir, '*')
        ch = glob.glob(res)
        return len(ch)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test00Help(ut.TestCase):

    def test00_mh(self):
        projs[0]._run(['-h'])

    def test01_mmhelp(self):
        projs[0]._run(['--help'])

    def test02_cmd_mhelp(self):
        for c, aliases in main.cmds.items():
            if c == 'help':
                continue
            projs[0]._run([c, '-h'])

    def test03_cmd_mmhelp(self):
        for c, aliases in main.cmds.items():
            if c == 'help':
                continue
            projs[0]._run([c, '--help'])


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test01Configure(ut.TestCase):

    def test00_default(self):
        run_projs(self, ['c'], lambda tb: tb.checkc(self))

    def test01_custom_dirs(self):
        run_projs(self, ['c'], lambda tb: tb.checkc(self))


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test02Build(ut.TestCase):

    def test00_default(self):
        run_projs(self, ['b'], lambda tb: tb.checkb(self))


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test03Install(ut.TestCase):

    def test00_default(self):
        run_projs(self, ['i'], lambda tb: tb.checki(self))


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
