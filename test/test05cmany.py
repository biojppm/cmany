#!/usr/bin/env python3

import unittest as ut
import subtest_fix
import os
import sys
import glob
import argparse
import copy
import tempfile
from itertools import combinations

import c4.cmany as cmany
import c4.cmany.util as util
import c4.cmany.main as main
import c4.cmany.cmake as cmake

from multiprocessing import cpu_count as cpu_count

srcdir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
sys.path.insert(0, srcdir)
maincmd = [sys.executable, '-m', 'c4.cmany.main', '--show-args']

projdir = os.path.dirname(__file__)
compiler_set = os.environ.get('CMANY_TEST_COMPILERS', None)
build_types = os.environ.get('CMANY_TEST_BUILDTYPES', 'Debug,Release')
test_projs = os.environ.get('CMANY_TEST_PROJS', 'hello,libhello')
proj_targets = {
    'hello': {
        'lib': [],
        'exe': ['hello'],
    },
    'libhello': {
        'lib': ['hello', 'hello_static'],
        'exe': ['test_hello', 'test_hello_static'],
    },
}
flag_bundle_set = {
    'none': {
        'spec': 'none',
        'expected': {
            'none': {'vars': [], 'defines': [], 'cxxflags': [], 'flags': [], },
        },
    },
    'foo': {
        'spec': '\'foo: -V FOO_VAR=1 -D FOO_DEF=1 -X "wall" -C "wall"\'',
        'expected': {
            'foo': {'vars': ['FOO_VAR=1'], 'defines': ['FOO_DEF=1'], 'cxxflags': ['wall'], 'flags': ['wall'], },
        },
    },
    'bar': {
        'spec': '\'bar: -V BAR_VAR=1 -D BAR_DEF=1 -X "g3" -C "g3"\'',
        'expected': {
            'bar': {'vars': ['BAR_VAR=1'], 'defines': ['BAR_DEF=1'], 'cxxflags': ['g3'], 'flags': ['g3'], },
        },
    },
}
variant_set = [flag_bundle_set[v]['spec'] for v in ('none', 'foo', 'bar')]

variant_tests = {
    'variant_test00-null':[],
    'variant_test01-none_explicit':['none'],

    'variant_test10-foo_only':['foo'],
    'variant_test11-none_foo':['none', 'foo'],

    'variant_test20-bar_only':['bar'],
    'variant_test21-none_bar':['none', 'bar'],

    'variant_test30-foobar_only':['foo', 'bar'],
    'variant_test31-foobar_only':['none', 'foo', 'bar'],
}


def _get_variant_spec(test_name):
    blueprint = variant_tests[test_name]
    if not blueprint:
        return []
    li = ['-v'] + [','.join(flag_bundle_set[v]['spec']) for v in blueprint]
    variants = cmany.Variant.create_variants(li)
    return li, variants


# unset environment variables which affect the behaviour of child invokations
# of cmany
os.environ['CMANY_ARGS'] = ''
os.environ['CMANY_PFX_ARGS'] = ''


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
        args = maincmd + args
        with util.setcwd(root):
            tmpfile, tmpname = tempfile.mkstemp(prefix="_cmany_tmp.out.")
            with util.stdout_redirected(tmpfile):
                #print("----->run():", self.proj, "at", os.getcwd(), " ".join(args))
                util.runsyscmd(args)
                #print("----->finished run():", self.proj, "at", os.getcwd(), " ".join(args))
            # close the mkstemp handle
            outsock = os.fdopen(tmpfile, "r")
            outsock.close()
            # read the input
            with open(tmpname, "r") as fh:
                output = fh.read()
            # remove the tmpfile
            os.remove(tmpname)
            #print("\n"*2, self.root, args[4:], "output len=", len(output), output[:min(len(output), 256)]+".................\n\n")
        return output


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

variant_set = cmany.Variant.create_variants(variant_set)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
def run_projs(testobj, args, check_fn=None):
    numbuilds = len(compiler_set) * len(build_types) * len(variant_set)
    #
    # run with default parameters
    bd = '.test/0--default--build'
    id = '.test/0--default--install'
    for p in projs:
        with testobj.subTest(msg="default parameters", proj=p.proj):
            p.run(args + ['--build-root', bd, '--install-root', id])
            if check_fn:
                tb = TestBuild(proj=p, buildroot=bd, installroot=id,
                               compiler=cmany.Compiler.default(),
                               build_type=cmany.BuildType.default(),
                               variant=cmany.Variant.default(),
                               numbuilds=1)
                check_fn(tb)
    #
    # run with default parameters in a non root dir
    rd = '.test/1--non_root_dir'
    for p in projs:
        with testobj.subTest(msg="run in a non root dir", proj=p.proj):
            p.run(args, custom_root=rd)
            if check_fn:
                tb = TestBuild(proj=p, buildroot=bd, installroot=id,
                               compiler=cmany.Compiler.default(),
                               build_type=cmany.BuildType.default(),
                               variant=cmany.Variant.default(),
                               numbuilds=1)
                check_fn(tb)
    #
    if numbuilds == 1:
        return
    #
    # run all sys,arch,compiler,buildtype,variant combinations at once
    bd = '.test/2.1--comps{}--types{}--variants{}--build'.format(len(compiler_set), len(build_types), len(variant_set))
    id = '.test/2.1--comps{}--types{}--variants{}--install'.format(len(compiler_set), len(build_types), len(variant_set))
    for p in projs:
        with testobj.subTest(msg="run all combinations at once", proj=p.proj):
            p.run(args + ['--build-root', bd,
                          '--install-root', id,
                          '-c', ','.join([c.name if c.is_msvc else c.path for c in compiler_set]),
                          '-t', ','.join([str(b) for b in build_types]),
                          '-v', ','.join([v.full_specs for v in variant_set])
            ])
            if check_fn:
                for c in compiler_set:
                    for t in build_types:
                        for v in variant_set:
                            tb = TestBuild(proj=p, buildroot=bd, installroot=id,
                                           compiler=c, build_type=t, variant=v,
                                           numbuilds=numbuilds)
                            check_fn(tb)
    #
    # run all sys,arch,compiler,buildtype,variant combinations at once - envargs
    bd = '.test/2.2--comps{}--types{}--variants{}--build'.format(len(compiler_set), len(build_types), len(variant_set))
    id = '.test/2.2--comps{}--types{}--variants{}--install'.format(len(compiler_set), len(build_types), len(variant_set))
    for p in projs:
        with testobj.subTest(msg="run all combinations at once", proj=p.proj):
            os.environ['CMANY_ARGS'] = '-c {} -t {} -v {}'.format(
                ','.join([c.name if c.is_msvc else c.path for c in compiler_set]),
                ','.join([str(b) for b in build_types]),
                ','.join([v.full_specs for v in variant_set])
            )
            #util.logwarn('export CMANY_ARGS={}'.format(os.environ['CMANY_ARGS']))
            p.run(args + ['--build-root', bd,
                          '--install-root', id,
            ])
            os.environ['CMANY_ARGS'] = ''
            if check_fn:
                for c in compiler_set:
                    for t in build_types:
                        for v in variant_set:
                            tb = TestBuild(proj=p, buildroot=bd, installroot=id,
                                           compiler=c, build_type=t, variant=v,
                                           numbuilds=numbuilds)
                            check_fn(tb)
    #
    # run sys,arch,compiler,buildtype combinations individually
    for p in projs:
        for c in compiler_set:
            for t in build_types:
                for v in variant_set:
                    with testobj.subTest(msg="run all combinations individually",
                                         proj=p.proj, compiler=c, build_type=t, variant=v):
                        bd = '.test/3.1--{}--{}--{}--build'.format(c, t, v.name)
                        id = '.test/3.1--{}--{}--{}--install'.format(c, t, v.name)
                        p.run(args + ['--build-root', bd,
                                      '--install-root', id,
                                      '-c', c.name if c.is_msvc else c.path,
                                      '-t', str(t),
                                      '-v', v.full_specs,
                        ])
                        if check_fn:
                            tb = TestBuild(proj=p, buildroot=bd, installroot=id,
                                           compiler=c, build_type=t, variant=v,
                                           numbuilds=1)
                            check_fn(tb)
    #
    # run sys,arch,compiler,buildtype combinations individually - envargs
    for p in projs:
        for c in compiler_set:
            for t in build_types:
                for v in variant_set:
                    with testobj.subTest(msg="run all combinations individually - envargs",
                                         proj=p.proj, compiler=c, build_type=t, variant=v):
                        bd = '.test/3.2--envargs--{}--{}--{}--build'.format(c, t, v.name)
                        id = '.test/3.2--envargs--{}--{}--{}--install'.format(c, t, v.name)
                        os.environ['CMANY_ARGS'] = '-c {} -t {} -v {}'.format(
                            c.name if c.is_msvc else c.path,
                            str(t),
                            v.full_specs)
                        #util.logwarn('export CMANY_ARGS={}'.format(os.environ['CMANY_ARGS']))
                        p.run(args + ['--build-root', bd, '--install-root', id])
                        os.environ['CMANY_ARGS'] = ''
                        if check_fn:
                            tb = TestBuild(proj=p, buildroot=bd, installroot=id,
                                           compiler=c, build_type=t, variant=v,
                                           numbuilds=1)
                            check_fn(tb)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class TestBuild:

    def __init__(self, proj, buildroot, installroot, compiler, build_type, variant, numbuilds):
        self.proj = proj
        self.buildroot = buildroot
        self.installroot = installroot
        self.compiler = compiler
        self.build_type = build_type
        self.variant = variant
        self.numbuilds = numbuilds
        self.flags = cmany.BuildFlags('all_builds')
        self.build_obj = cmany.Build(proj_root=self.proj.root,
                                     build_root=os.path.join(self.proj.root, self.buildroot),
                                     install_root=os.path.join(self.proj.root, self.installroot),
                                     system=cmany.System.default(),
                                     arch=cmany.Architecture.default(),
                                     build_type=build_type,
                                     compiler=compiler,
                                     variant=variant,
                                     flags=self.flags,
                                     num_jobs=cpu_count(),
                                     kwargs={}
                                     )

    def checkc(self, tester):
        tester.assertEqual(self.nsiblings(self.buildroot), self.numbuilds, msg=self.buildroot + str(self.siblings(self.buildroot)))
        build_type = cmake.getcachevar(self.build_obj.builddir, 'CMAKE_BUILD_TYPE')
        tester.assertEqual(build_type, str(self.build_type))

    def checkv(self, tester):
        pass

    def checkb(self, tester):
        self.checkc(tester)

    def checki(self, tester):
        tester.assertEqual(self.nsiblings(self.installroot), self.numbuilds)

    def nsiblings(self, dir):
        return len(self.siblings(dir))

    def siblings(self, dir):
        res = os.path.join(self.proj.root, dir, '*')
        ch = glob.glob(res)
        return ch



# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class Outputs(dict):

    "a class to store several outputs which should be the same"

    def add_one(self, k, kk, vv):
        l = self.get(k)
        if l is None:
            l = []
            self[k] = l
        l.append((kk, vv))

    def compare_outputs(self, test):
        for k, outs in self.items():
            rk, rv = outs[0]
            rv = self._filter_output(rv)
            for kk, vv in outs[1:]:
                vv = self._filter_output(vv)
                test.assertEqual(rv, vv, "{}: refkey: '{}' vs key '{}'".format(k, rk, kk))

    def _filter_output(self, s):
        # the first three lines contain the command, so skip them
        out = "\n".join(s.split("\n")[3:])
        return out


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Test00Help(ut.TestCase):

    # TODO: grab the output and compare it to make sure it is the same

    def setUp(self):
        super().setUp()
        self.maxDiff = None
        # make sure --show-args is not used to projs.run()
        global maincmd
        self.maincmd = maincmd
        maincmd = [c for c in maincmd if c != '--show-args']
    def tearDown(self):
        super().tearDown()
        global maincmd
        maincmd = self.maincmd


    cmany_help = Outputs()
    def test00_cmany_help_short(self):
        out = projs[0].run(['-h'])
        __class__.cmany_help.add_one('-h', '-h', out)
    def test01_cmany_help_long(self):
        out = projs[0].run(['--help'])
        __class__.cmany_help.add_one('-h', '--help', out)
    def test0x_cmany_help_compare(self):
        __class__.cmany_help.compare_outputs(self)


    sc_help_short = Outputs()
    def test10_subcommand_help_short(self):
        for c, aliases in main.cmds.items():
            if c == 'help': continue
            out = projs[0].run([c, '-h'])
            __class__.sc_help_short.add_one(c, c, out)
    def test11_subcommand_help_short_aliases(self):
        for c, aliases in main.cmds.items():
            if c == 'help': continue
            for a in aliases:
                out = projs[0].run([a, '-h'])
                __class__.sc_help_short.add_one(c, a, out)
    def test1x_subcommand_help_compare(self):
        __class__.sc_help_short.compare_outputs(self)


    sc_help_short_rev = Outputs()
    def test20_subcommand_help_short_rev(self):
        for c, aliases in main.cmds.items():
            if c == 'help': continue
            out = projs[0].run(['h', c])
            __class__.sc_help_short_rev.add_one(c, c, out)
    def test21_subcommand_help_short_rev_aliases(self):
        for c, aliases in main.cmds.items():
            if c == 'help': continue
            for a in aliases:
                out = projs[0].run(['h', a])
                __class__.sc_help_short_rev.add_one(c, a, out)
    def test2x_subcommand_help_compare(self):
        __class__.sc_help_short_rev.compare_outputs(self)


    sc_help_long = Outputs()
    def test30_subcommand_help_long(self):
        for c, aliases in main.cmds.items():
            if c == 'help': continue
            out = projs[0].run([c, '--help'])
            __class__.sc_help_long.add_one(c, c, out)
    def test31_subcommand_help_long_aliases(self):
        for c, aliases in main.cmds.items():
            if c == 'help': continue
            for a in aliases:
                out = projs[0].run([a, '--help'])
                __class__.sc_help_long.add_one(c, a, out)
    def test3x_subcommand_help_long_compare(self):
        __class__.sc_help_long.compare_outputs(self)


    sc_help_long_rev = Outputs()
    def test40_subcommand_help_long_rev(self):
        for c, aliases in main.cmds.items():
            if c == 'help': continue
            out = projs[0].run(['help', c])
            __class__.sc_help_long_rev.add_one(c, c, out)
    def test41_subcommand_help_long_rev_aliases(self):
        for c, aliases in main.cmds.items():
            if c == 'help': continue
            for a in aliases:
                out = projs[0].run(['help', a])
                __class__.sc_help_long_rev.add_one(c, a, out)
    def test4x_subcommand_help_long_compare(self):
        __class__.sc_help_long_rev.compare_outputs(self)


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


class Test04Dependencies(ut.TestCase):
    pass

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    ut.main()
