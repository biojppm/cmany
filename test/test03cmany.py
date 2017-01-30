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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
maincmd = [sys.executable, '-m', 'c4.cmany.main']

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
class Test20Flags(ut.TestCase):

    def test01_cmake_vars(self):
        self._do_separate_test('-V', '--vars')

    def test02_defines(self):
        self._do_separate_test('-D', '--defines')

    def test03_cxxflags(self):
        self._do_separate_test('-X', '--cxxflags')

    def test04_cflags(self):
        self._do_separate_test('-C', '--cflags')

    def _do_separate_test(self, shortopt, longopt):
        n = longopt[2:]
        for o in (shortopt, longopt):
            def _c(a, r): self.check_one(n, o, a, r)
            _c('{} VAR1', ['VAR1'])
            _c('{} VAR2,VAR3', ['VAR2', 'VAR3'])
            _c('{} VAR4 {} VAR5', ['VAR4', 'VAR5'])
            _c('{} VAR6,VAR7 {} VAR8,VAR9', ['VAR6', 'VAR7', 'VAR8', 'VAR9'])
            _c('{} VAR\,1', ['VAR,1'])
            _c('{} VAR\,2,VAR\,3', ['VAR,2', 'VAR,3'])
            _c('{} VAR\,4 {} VAR\,5', ['VAR,4', 'VAR,5'])
            _c('{} VAR\,6,VAR\,7 {} VAR\,8,VAR\,9', ['VAR,6', 'VAR,7', 'VAR,8', 'VAR,9'])
            _c('{} VAR1=1', ['VAR1=1'])
            _c('{} VAR2=2,VAR3=3', ['VAR2=2', 'VAR3=3'])
            _c('{} VAR4=4 {} VAR5=5', ['VAR4=4', 'VAR5=5'])
            _c('{} VAR6=6,VAR7=7 {} VAR8=8,VAR9=9', ['VAR6=6', 'VAR7=7', 'VAR8=8', 'VAR9=9'])
            _c('{} VAR1=1\,a', ['VAR1=1,a'])
            _c('{} VAR2=2\,a,VAR3=3\,a', ['VAR2=2,a', 'VAR3=3,a'])
            _c('{} VAR4=4\,a {} VAR5=5\,a', ['VAR4=4,a', 'VAR5=5,a'])
            _c('{} VAR6=6\,a,VAR7=7\,a {} VAR8=8\,a,VAR9=9\,a', ['VAR6=6,a', 'VAR7=7,a', 'VAR8=8,a', 'VAR9=9,a'])
            _c(['{}', 'VAR1="1 with spaces"'], ['VAR1="1 with spaces"'])
            _c(['{}', 'VAR2="2 with spaces",VAR3="3 with spaces"'], ['VAR2="2 with spaces"', 'VAR3="3 with spaces"'])
            _c(['{}', 'VAR4="4 with spaces"', '{}', 'VAR5="5 with spaces"'], ['VAR4="4 with spaces"', 'VAR5="5 with spaces"'])
            _c(['{}', 'VAR6="6 with spaces",VAR7="7 with spaces"', '{}', 'VAR8="8 with spaces",VAR9="9 with spaces"'], ['VAR6="6 with spaces"', 'VAR7="7 with spaces"', 'VAR8="8 with spaces"', 'VAR9="9 with spaces"'])
            _c(['{}', 'VAR1="1\,a with spaces"'], ['VAR1="1,a with spaces"'])
            _c(['{}', 'VAR2="2\,a with spaces",VAR3="3\,a with spaces"'], ['VAR2="2,a with spaces"', 'VAR3="3,a with spaces"'])
            _c(['{}', 'VAR4="4\,a with spaces"', '{}', 'VAR5="5\,a with spaces"'], ['VAR4="4,a with spaces"', 'VAR5="5,a with spaces"'])
            _c(['{}', 'VAR6="6\,a with spaces",VAR7="7\,a with spaces"', '{}', 'VAR8="8\,a with spaces",VAR9="9\,a with spaces"'], ['VAR6="6,a with spaces"', 'VAR7="7,a with spaces"', 'VAR8="8,a with spaces"', 'VAR9="9,a with spaces"'])
            _c('{} "-fPIC,-Wall,-O3,-Os"', ['-fPIC', '-Wall', '-O3', '-Os'])
            _c("{} '-fPIC,-Wall,-O3,-Os'", ['-fPIC', '-Wall', '-O3', '-Os'])
            _c('{} "-fPIC","-Wall","-O3","-Os"', ['-fPIC', '-Wall', '-O3', '-Os'])
            _c("{} '-fPIC','-Wall','-O3','-Os'", ['-fPIC', '-Wall', '-O3', '-Os'])

    def check_one(self, name, opt, args, ref):
        if isinstance(args, str):
            args = args.split(' ')
        args_ = args
        args = []
        for a in args_:
            args.append(a.format(opt))
        p = argparse.ArgumentParser()
        main.add_flag_opts(p)
        out = p.parse_args(args)
        # print(out, kwargs)
        a = getattr(out, name)
        self.assertEqual(ref, a)
        del out

    def check_many(self, args, **ref):
        if isinstance(args, str):
            args = util.splitesc_quoted(args, ' ')
        p = argparse.ArgumentParser()
        main.add_flag_opts(p)
        out = p.parse_args(args)
        # print(out, kwargs)
        for k, refval in ref.items():
            result = getattr(out, k)
            self.assertEqual(result, refval)
        del out

    def test10_mixed0(self):
        self.check_many('-X "-fPIC" -D VARIANT1', vars=[], cxxflags=['-fPIC'], cflags=[], defines=['VARIANT1'])
        self.check_many('-X "-Wall" -D VARIANT2', vars=[], cxxflags=['-Wall'], cflags=[], defines=['VARIANT2'])
        self.check_many('-X nortti,c++14 -D VARIANT3', vars=[], cxxflags=['nortti', 'c++14'], cflags=[], defines=['VARIANT3'])
        self.check_many('-X "-fPIC,-Wl\,-rpath" -D VARIANT1', vars=[], cxxflags=['-fPIC','-Wl,-rpath'], cflags=[], defines=['VARIANT1'])

    def test11_mixed1(self):
        self.check_many('-X "-fPIC" -D VARIANT1,VARIANT_TYPE=1', vars=[], cxxflags=['-fPIC'], cflags=[], defines=['VARIANT1', 'VARIANT_TYPE=1'])
        self.check_many('-X "-Wall" -D VARIANT2,VARIANT_TYPE=2', vars=[], cxxflags=['-Wall'], cflags=[], defines=['VARIANT2', 'VARIANT_TYPE=2'])
        self.check_many('-X nortti,c++14 -D VARIANT3,VARIANT_TYPE=3', vars=[], cxxflags=['nortti', 'c++14'], cflags=[], defines=['VARIANT3', 'VARIANT_TYPE=3'])

    def test12_mixed2(self):
        self.check_many('-X "-fPIC" -D VARIANT1,"VARIANT_TYPE=1"', vars=[], cxxflags=['-fPIC'], cflags=[], defines=['VARIANT1', 'VARIANT_TYPE=1'])
        self.check_many('-X "-Wall" -D VARIANT2,"VARIANT_TYPE=2"', vars=[], cxxflags=['-Wall'], cflags=[], defines=['VARIANT2', 'VARIANT_TYPE=2'])
        self.check_many('-X nortti,c++14 -D VARIANT3,"VARIANT_TYPE=3"', vars=[], cxxflags=['nortti', 'c++14'], cflags=[], defines=['VARIANT3', 'VARIANT_TYPE=3'])

    def test13_mixed3(self):
        self.check_many('-X "-fPIC" -D "VARIANT1,VARIANT_TYPE=1"', vars=[], cxxflags=['-fPIC'], cflags=[], defines=['VARIANT1', 'VARIANT_TYPE=1'])
        self.check_many('-X "-Wall" -D "VARIANT2,VARIANT_TYPE=2"', vars=[], cxxflags=['-Wall'], cflags=[], defines=['VARIANT2', 'VARIANT_TYPE=2'])
        self.check_many('-X nortti,c++14 -D "VARIANT3,VARIANT_TYPE=3"', vars=[], cxxflags=['nortti', 'c++14'], cflags=[], defines=['VARIANT3', 'VARIANT_TYPE=3'])


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
