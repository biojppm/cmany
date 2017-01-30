#!/usr/bin/env python3

import unittest as ut
import os
import sys
import glob
import argparse
import copy
from itertools import combinations

import c4.cmany.util as util
import c4.cmany.main as main
import c4.cmany.cmany as cmany
import c4.cmany.cmake as cmake

srcdir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
sys.path.insert(0, srcdir)
maincmd = [sys.executable, '-m', 'c4.cmany.main', '--show-args']

projdir = os.path.dirname(__file__)
compiler_set = os.environ.get('CMANY_TEST_COMPILERS', None)
build_types = os.environ.get('CMANY_TEST_BUILDTYPES', 'Debug,Release')
test_projs = os.environ.get('CMANY_TEST_PROJS', 'hello,libhello')
proj_targets = {
    'hello':{
        'lib':[],
        'exe':['hello'],
    },
    'libhello':{
        'lib':['hello','hello_static'],
        'exe':['test_hello','test_hello_static'],
    },
}


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class CMakeTestProj:

    def __init__(self, proj):
        self.proj = proj
        self.root = util.chkf(projdir, proj)
        if proj_targets.get(proj) is None:
            raise Exception("no target info for project " + proj)
        self.libs = proj_targets[proj]['lib']
        self.exes = proj_targets[proj]['exe']
        self.targets = self.libs + self.exes
        self.multi_target = (len(self.targets) > 1)
        # http://stackoverflow.com/questions/17176887/python-get-all-permutation-of-a-list-w-o-repetitions
        self.target_combinations = []
        for i in range(1, len(self.targets) + 1):
            self.target_combinations += list(combinations(self.targets, i))

    def run(self, args_, custom_root=None):
        args = copy.deepcopy(args_)
        root = self.root
        if custom_root is not None:
            with util.setcwd(self.root):
                root = os.path.abspath(custom_root)
                if not os.path.exists(root):
                    os.makedirs(root)
                projdir = os.path.abspath('.')
                args.append(projdir)
        with util.setcwd(root):
            args = maincmd + args
            #print("----->run():", self.proj, "at", os.getcwd(), " ".join(args))
            util.runsyscmd(args)
            #print("----->finished run():", self.proj, "at", os.getcwd(), " ".join(args))


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

    # run with default parameters
    bd = '.test/0--default--build'
    id = '.test/0--default--install'
    for p in projs:
        with testobj.subTest(msg="default parameters", proj=p.proj):
            p.run(args + ['--build-dir', bd, '--install-dir', id])
            if check_fn:
                tb = TestBuild(proj=p, buildroot=bd, installroot=id,
                               compiler=cmany.Compiler.default(),
                               buildtype=cmany.BuildType.default(),
                               numbuilds=1)
                check_fn(tb)

    # run in a non root dir
    rd = '.test/1--non_root_dir'
    for p in projs:
        with testobj.subTest(msg="run in a non root dir", proj=p.proj):
            p.run(args, custom_root=rd)
            if check_fn:
                tb = TestBuild(proj=p, buildroot=bd, installroot=id,
                               compiler=cmany.Compiler.default(),
                               buildtype=cmany.BuildType.default(),
                               numbuilds=1)
                check_fn(tb)

    if numbuilds == 1:
        return

    # run all sys,arch,compiler,buildtype combinations at once
    bd = '.test/2--comps{}--types{}--build'.format(len(compiler_set), len(build_types))
    id = '.test/2--comps{}--types{}--install'.format(len(compiler_set), len(build_types))
    for p in projs:
        with testobj.subTest(msg="run all combinations at once", proj=p.proj):
            p.run(args + ['--build-dir', bd,
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

    # run sys,arch,compiler,buildtype combinations individually
    for p in projs:
        with testobj.subTest(msg="run all combinations individually", proj=p.proj):
            for c in compiler_set:
                for t in build_types:
                    bd = '.test/3--{}--{}--build'.format(c, t)
                    id = '.test/3--{}--{}--install'.format(c, t)
                    p.run(args + ['--build-dir', bd,
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
        self.flags = cmany.BuildFlags('all_builds')
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
        projs[0].run(['-h'])

    def test01_mmhelp(self):
        projs[0].run(['--help'])

    def test02_cmd_mhelp(self):
        for c, aliases in main.cmds.items():
            if c == 'help':
                continue
            projs[0].run([c, '-h'])

    def test03_cmd_mmhelp(self):
        for c, aliases in main.cmds.items():
            if c == 'help':
                continue
            projs[0].run([c, '--help'])


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
if __name__ == '__main__':
    ut.main()
