#!/usr/bin/env python3

import unittest as ut
from parameterized import parameterized

import os.path as osp
import shutil
import os

import c4.cmany.util as util
import c4.cmany.err as err
import c4.cmany.cmake as c4cmake

from collections import OrderedDict as odict


srcdir = osp.abspath(osp.dirname(__file__))
dstdir = osp.join(osp.join(srcdir, 'hello/.test/'), '0--cache')
src = osp.join(srcdir, 'CMakeCache.txt')
dst = osp.join(dstdir, 'CMakeCache.txt')
validtypes = ["STRING", "PATH", "FILEPATH", "BOOL", "STATIC", "INTERNAL"]


def _clear_cache():
    if osp.exists(dst):
        os.remove(dst)
    assert not osp.exists(dst), dst
    return dstdir


def _setup_cache():
    _clear_cache()
    os.makedirs(dstdir, exist_ok=True)
    assert osp.exists(dstdir), dstdir
    assert src != dst
    shutil.copy(src, dst)
    assert osp.exists(dst), dst
    return dstdir


# -----------------------------------------------------------------------------

class Test00has_cache(ut.TestCase):

    def test_00detects_existing(self):
        dir = _setup_cache()
        self.assertTrue(c4cmake.hascache(dir), dir)

    def test_01detects_missing(self):
        dir = _clear_cache()
        self.assertFalse(c4cmake.hascache(dir), dir)


# -----------------------------------------------------------------------------

"""
1 CMAKE_AR FILEPATH /usr/bin/ar
2 CMAKE_BUILD_TYPE STRING
3 CMAKE_COLOR_MAKEFILE BOOL ON
4 CMAKE_CXX_COMPILER FILEPATH /usr/bin/c++
5 CMAKE_CXX_COMPILER_AR FILEPATH /usr/bin/gcc-ar
6 CMAKE_CXX_COMPILER_RANLIB FILEPATH /usr/bin/gcc-ranlib
7 CMAKE_CXX_FLAGS STRING
8 CMAKE_CXX_FLAGS_DEBUG STRING -g
9 CMAKE_CXX_FLAGS_MINSIZEREL STRING -Os -DNDEBUG
10 CMAKE_CXX_FLAGS_RELEASE STRING -O3 -DNDEBUG
11 CMAKE_CXX_FLAGS_RELWITHDEBINFO STRING -O2 -g -DNDEBUG
12 CMAKE_C_COMPILER FILEPATH /usr/bin/cc
13 CMAKE_C_COMPILER_AR FILEPATH /usr/bin/gcc-ar
14 CMAKE_C_COMPILER_RANLIB FILEPATH /usr/bin/gcc-ranlib
15 CMAKE_C_FLAGS STRING
16 CMAKE_C_FLAGS_DEBUG STRING -g
17 CMAKE_C_FLAGS_MINSIZEREL STRING -Os -DNDEBUG
18 CMAKE_C_FLAGS_RELEASE STRING -O3 -DNDEBUG
19 CMAKE_C_FLAGS_RELWITHDEBINFO STRING -O2 -g -DNDEBUG
20 CMAKE_DLLTOOL FILEPATH CMAKE_DLLTOOL-NOTFOUND
21 CMAKE_EXE_LINKER_FLAGS STRING
22 CMAKE_EXE_LINKER_FLAGS_DEBUG STRING
23 CMAKE_EXE_LINKER_FLAGS_MINSIZEREL STRING
24 CMAKE_EXE_LINKER_FLAGS_RELEASE STRING
25 CMAKE_EXE_LINKER_FLAGS_RELWITHDEBINFO STRING
26 CMAKE_EXPORT_COMPILE_COMMANDS BOOL
27 CMAKE_FIND_PACKAGE_REDIRECTS_DIR STATIC /home/usr/proj/cmany/test/hello/build/CMakeFiles/pkgRedirects
28 CMAKE_INSTALL_PREFIX PATH /usr/local
29 CMAKE_LINKER FILEPATH /usr/bin/ld
30 CMAKE_MAKE_PROGRAM FILEPATH /usr/bin/make
31 CMAKE_MODULE_LINKER_FLAGS STRING
32 CMAKE_MODULE_LINKER_FLAGS_DEBUG STRING
33 CMAKE_MODULE_LINKER_FLAGS_MINSIZEREL STRING
34 CMAKE_MODULE_LINKER_FLAGS_RELEASE STRING
35 CMAKE_MODULE_LINKER_FLAGS_RELWITHDEBINFO STRING
36 CMAKE_NM FILEPATH /usr/bin/nm
37 CMAKE_OBJCOPY FILEPATH /usr/bin/objcopy
38 CMAKE_OBJDUMP FILEPATH /usr/bin/objdump
39 CMAKE_PROJECT_DESCRIPTION STATIC
40 CMAKE_PROJECT_HOMEPAGE_URL STATIC
41 CMAKE_PROJECT_NAME STATIC hello
42 CMAKE_RANLIB FILEPATH /usr/bin/ranlib
43 CMAKE_READELF FILEPATH /usr/bin/readelf
44 CMAKE_SHARED_LINKER_FLAGS STRING
45 CMAKE_SHARED_LINKER_FLAGS_DEBUG STRING
46 CMAKE_SHARED_LINKER_FLAGS_MINSIZEREL STRING
47 CMAKE_SHARED_LINKER_FLAGS_RELEASE STRING
48 CMAKE_SHARED_LINKER_FLAGS_RELWITHDEBINFO STRING
49 CMAKE_SKIP_INSTALL_RPATH BOOL NO
50 CMAKE_SKIP_RPATH BOOL NO
51 CMAKE_STATIC_LINKER_FLAGS STRING
52 CMAKE_STATIC_LINKER_FLAGS_DEBUG STRING
53 CMAKE_STATIC_LINKER_FLAGS_MINSIZEREL STRING
54 CMAKE_STATIC_LINKER_FLAGS_RELEASE STRING
55 CMAKE_STATIC_LINKER_FLAGS_RELWITHDEBINFO STRING
56 CMAKE_STRIP FILEPATH /usr/bin/strip
57 CMAKE_VERBOSE_MAKEFILE BOOL FALSE
58 hello_BINARY_DIR STATIC /home/usr/proj/cmany/test/hello/build
59 hello_IS_TOP_LEVEL STATIC ON
60 hello_SOURCE_DIR STATIC /home/usr/proj/cmany/test/hello
61 CMAKE_ADDR2LINE-ADVANCED INTERNAL 1
62 CMAKE_AR-ADVANCED INTERNAL 1
63 CMAKE_CACHEFILE_DIR INTERNAL /home/usr/proj/cmany/test/hello/build
64 CMAKE_CACHE_MAJOR_VERSION INTERNAL 3
65 CMAKE_CACHE_MINOR_VERSION INTERNAL 25
66 CMAKE_CACHE_PATCH_VERSION INTERNAL 2
67 CMAKE_COLOR_MAKEFILE-ADVANCED INTERNAL 1
68 CMAKE_COMMAND INTERNAL /usr/bin/cmake
69 CMAKE_CPACK_COMMAND INTERNAL /usr/bin/cpack
70 CMAKE_CTEST_COMMAND INTERNAL /usr/bin/ctest
71 CMAKE_CXX_COMPILER-ADVANCED INTERNAL 1
72 CMAKE_CXX_COMPILER_AR-ADVANCED INTERNAL 1
73 CMAKE_CXX_COMPILER_RANLIB-ADVANCED INTERNAL 1
74 CMAKE_CXX_FLAGS-ADVANCED INTERNAL 1
75 CMAKE_CXX_FLAGS_DEBUG-ADVANCED INTERNAL 1
76 CMAKE_CXX_FLAGS_MINSIZEREL-ADVANCED INTERNAL 1
77 CMAKE_CXX_FLAGS_RELEASE-ADVANCED INTERNAL 1
78 CMAKE_CXX_FLAGS_RELWITHDEBINFO-ADVANCED INTERNAL 1
79 CMAKE_C_COMPILER-ADVANCED INTERNAL 1
80 CMAKE_C_COMPILER_AR-ADVANCED INTERNAL 1
81 CMAKE_C_COMPILER_RANLIB-ADVANCED INTERNAL 1
82 CMAKE_C_FLAGS-ADVANCED INTERNAL 1
83 CMAKE_C_FLAGS_DEBUG-ADVANCED INTERNAL 1
84 CMAKE_C_FLAGS_MINSIZEREL-ADVANCED INTERNAL 1
85 CMAKE_C_FLAGS_RELEASE-ADVANCED INTERNAL 1
86 CMAKE_C_FLAGS_RELWITHDEBINFO-ADVANCED INTERNAL 1
87 CMAKE_DLLTOOL-ADVANCED INTERNAL 1
88 CMAKE_EDIT_COMMAND INTERNAL /usr/bin/ccmake
89 CMAKE_EXECUTABLE_FORMAT INTERNAL ELF
90 CMAKE_EXE_LINKER_FLAGS-ADVANCED INTERNAL 1
91 CMAKE_EXE_LINKER_FLAGS_DEBUG-ADVANCED INTERNAL 1
92 CMAKE_EXE_LINKER_FLAGS_MINSIZEREL-ADVANCED INTERNAL 1
93 CMAKE_EXE_LINKER_FLAGS_RELEASE-ADVANCED INTERNAL 1
94 CMAKE_EXE_LINKER_FLAGS_RELWITHDEBINFO-ADVANCED INTERNAL 1
95 CMAKE_EXPORT_COMPILE_COMMANDS-ADVANCED INTERNAL 1
96 CMAKE_EXTRA_GENERATOR INTERNAL
97 CMAKE_GENERATOR INTERNAL Unix Makefiles
98 CMAKE_GENERATOR_INSTANCE INTERNAL
99 CMAKE_GENERATOR_PLATFORM INTERNAL
100 CMAKE_GENERATOR_TOOLSET INTERNAL
101 CMAKE_HOME_DIRECTORY INTERNAL /home/usr/proj/cmany/test/hello
102 CMAKE_INSTALL_SO_NO_EXE INTERNAL 0
103 CMAKE_LINKER-ADVANCED INTERNAL 1
104 CMAKE_MAKE_PROGRAM-ADVANCED INTERNAL 1
105 CMAKE_MODULE_LINKER_FLAGS-ADVANCED INTERNAL 1
106 CMAKE_MODULE_LINKER_FLAGS_DEBUG-ADVANCED INTERNAL 1
107 CMAKE_MODULE_LINKER_FLAGS_MINSIZEREL-ADVANCED INTERNAL 1
108 CMAKE_MODULE_LINKER_FLAGS_RELEASE-ADVANCED INTERNAL 1
109 CMAKE_MODULE_LINKER_FLAGS_RELWITHDEBINFO-ADVANCED INTERNAL 1
110 CMAKE_NM-ADVANCED INTERNAL 1
111 CMAKE_NUMBER_OF_MAKEFILES INTERNAL 1
112 CMAKE_OBJCOPY-ADVANCED INTERNAL 1
113 CMAKE_OBJDUMP-ADVANCED INTERNAL 1
114 CMAKE_PLATFORM_INFO_INITIALIZED INTERNAL 1
115 CMAKE_RANLIB-ADVANCED INTERNAL 1
116 CMAKE_READELF-ADVANCED INTERNAL 1
117 CMAKE_ROOT INTERNAL /usr/share/cmake
118 CMAKE_SHARED_LINKER_FLAGS-ADVANCED INTERNAL 1
119 CMAKE_SHARED_LINKER_FLAGS_DEBUG-ADVANCED INTERNAL 1
120 CMAKE_SHARED_LINKER_FLAGS_MINSIZEREL-ADVANCED INTERNAL 1
121 CMAKE_SHARED_LINKER_FLAGS_RELEASE-ADVANCED INTERNAL 1
122 CMAKE_SHARED_LINKER_FLAGS_RELWITHDEBINFO-ADVANCED INTERNAL 1
123 CMAKE_SKIP_INSTALL_RPATH-ADVANCED INTERNAL 1
124 CMAKE_SKIP_RPATH-ADVANCED INTERNAL 1
125 CMAKE_STATIC_LINKER_FLAGS-ADVANCED INTERNAL 1
126 CMAKE_STATIC_LINKER_FLAGS_DEBUG-ADVANCED INTERNAL 1
127 CMAKE_STATIC_LINKER_FLAGS_MINSIZEREL-ADVANCED INTERNAL 1
128 CMAKE_STATIC_LINKER_FLAGS_RELEASE-ADVANCED INTERNAL 1
129 CMAKE_STATIC_LINKER_FLAGS_RELWITHDEBINFO-ADVANCED INTERNAL 1
130 CMAKE_STRIP-ADVANCED INTERNAL 1
131 CMAKE_UNAME INTERNAL /usr/bin/uname
132 CMAKE_VERBOSE_MAKEFILE-ADVANCED INTERNAL 1
133 _CMAKE_LINKER_PUSHPOP_STATE_SUPPORTED INTERNAL TRUE
"""

class Test01guess_var_type(ut.TestCase):

    def test_00internal(self):
        self.assertEqual(c4cmake._guess_var_type("CMAKE_NM-ADVANCED", "1"), "INTERNAL")
        self.assertEqual(c4cmake._guess_var_type("CMAKE_SHARED_LINKER_FLAGS-ADVANCED", "1"), "INTERNAL")

    def test_01bool(self):
        self.assertEqual(c4cmake._guess_var_type("foo", "ON"), "BOOL")
        self.assertEqual(c4cmake._guess_var_type("foo", "OFF"), "BOOL")
        self.assertEqual(c4cmake._guess_var_type("foo", "YES"), "BOOL")
        self.assertEqual(c4cmake._guess_var_type("foo", "NO"), "BOOL")
        self.assertEqual(c4cmake._guess_var_type("foo", "1"), "BOOL")
        self.assertEqual(c4cmake._guess_var_type("foo", "0"), "BOOL")
        self.assertEqual(c4cmake._guess_var_type("foo", "TRUE"), "BOOL")
        self.assertEqual(c4cmake._guess_var_type("foo", "FALSE"), "BOOL")
        self.assertEqual(c4cmake._guess_var_type("foo", "T"), "BOOL")
        self.assertEqual(c4cmake._guess_var_type("foo", "F"), "BOOL")
        self.assertEqual(c4cmake._guess_var_type("foo", "N"), "BOOL")
        self.assertEqual(c4cmake._guess_var_type("foo", "Y"), "BOOL")
        self.assertEqual(c4cmake._guess_var_type("CMAKE_EXPORT_COMPILE_COMMANDS", None), "BOOL")
        self.assertEqual(c4cmake._guess_var_type("CMAKE_EXPORT_COMPILE_COMMANDS", "ON"), "BOOL")
        self.assertEqual(c4cmake._guess_var_type("CMAKE_EXPORT_COMPILE_COMMANDS", "1"), "BOOL")

    def test_10full(self):
        cachedict = c4cmake.loadvars(_setup_cache())
        self.assertGreater(len(cachedict), 0)
        for i, (k, v) in enumerate(cachedict.items()):
            #print(i, k, v.vartype, v.val)
            self.assertEqual(k, v.name)
            self.assertEqual(c4cmake._guess_var_type(v.name, v.val), v.vartype, v.name)


# -----------------------------------------------------------------------------
class Test02CMakeCacheVar(ut.TestCase):

    def test_00default_args(self):
        v = c4cmake.CMakeCacheVar("foo", "bar")
        self.assertEqual(v.name, "foo")
        self.assertEqual(v.val, "bar")
        self.assertEqual(v.vartype, "STRING")
        self.assertEqual(v.dirty, False)
        self.assertEqual(v.from_input, False)

    def test_01vartype_is_correct(self):
        """set the variable without the vartype, then check it is correctly guessed"""
        cachedict = c4cmake.loadvars(_setup_cache())
        self.assertGreater(len(cachedict), 0)
        for i, (k, v) in enumerate(cachedict.items()):
            vnew = c4cmake.CMakeCacheVar(v.name, v.val)
            self.assertEqual(vnew.vartype, v.vartype, v.name)

    def test_10reset_val_taints(self):
        v = c4cmake.CMakeCacheVar("foo", "bar", "STRING")
        self.assertEqual(v.name, "foo")
        self.assertEqual(v.val, "bar")
        self.assertEqual(v.vartype, "STRING")
        self.assertFalse(v.dirty)
        self.assertFalse(v.from_input)
        v.reset(val="newval")
        self.assertTrue(v.dirty)

    def test_11reset_same_val_preserves(self):
        v = c4cmake.CMakeCacheVar("foo", "bar", "STRING")
        self.assertEqual(v.name, "foo")
        self.assertEqual(v.val, "bar")
        self.assertEqual(v.vartype, "STRING")
        self.assertFalse(v.dirty)
        self.assertFalse(v.from_input)
        v.reset(val=v.val)
        self.assertFalse(v.dirty)

    def test_20reset_type_fails(self):
        v = c4cmake.CMakeCacheVar("foo", "bar", "STRING")
        self.assertEqual(v.name, "foo")
        self.assertEqual(v.val, "bar")
        self.assertEqual(v.vartype, "STRING")
        self.assertFalse(v.dirty)
        with self.assertRaises(err.CannotChangeCacheVarType) as cm:
            v.reset(val="foo", vartype="FILEPATH")


# -----------------------------------------------------------------------------

class Test03loadvars(ut.TestCase):

    def test_00empty_when_cache_missing(self):
        v = c4cmake.loadvars(_clear_cache())
        self.assertEqual(len(v), 0)

    def test_01non_empty_when_cache_exists(self):
        v = c4cmake.loadvars(_setup_cache())
        self.assertGreater(len(v), 0)

    def test_02all_members_are_CMakeVar(self):
        cachedict = c4cmake.loadvars(_setup_cache())
        self.assertGreater(len(cachedict), 0)
        for k, v in cachedict.items():
            self.assertTrue(isinstance(v, c4cmake.CMakeCacheVar))

    def test_03all_vars_are_set(self):
        cachedict = c4cmake.loadvars(_setup_cache())
        self.assertGreater(len(cachedict), 0)
        for i, (k, v) in enumerate(cachedict.items()):
            #print(i, k, v.vartype, v.val)
            self.assertTrue(isinstance(v, c4cmake.CMakeCacheVar))
            self.assertEqual(k, v.name)
            self.assertFalse(v.dirty)
            self.assertFalse(v.from_input)
            self.assertIn(v.vartype, validtypes, v.name)


# -----------------------------------------------------------------------------

class Test04setcachevars(ut.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dir = _setup_cache()
        self.original = c4cmake.loadvars(self.dir)

    def _set_and_load(self, varvalues):
        c4cmake.setcachevars(self.dir, varvalues)
        return c4cmake.loadvars(self.dir)

    def test_00_mutate_existing_val_succeeds(self):
        name = "CMAKE_C_FLAGS" # use this because there are several other vars with the same prefix
        self.assertIn(name, self.original.keys())
        result = self._set_and_load({
            name: self.original[name].val + ".changed",
        })
        self.assertNotEqual(result[name].val, self.original[name].val)
        self.assertEqual(result[name].vartype, self.original[name].vartype)
        # check no entries were added/removed
        self.assertEqual(len(result.keys()), len(self.original.keys()))
        self.assertEqual(list(sorted(result.keys())), list(sorted(self.original.keys())))
        for k, v in result.items():
            if k == name:
                self.assertNotEqual(v.val, self.original[k].val)
                self.assertEqual(v.vartype, self.original[k].vartype)
            else:
                self.assertEqual(v.val, self.original[k].val)
                self.assertEqual(v.vartype, self.original[k].vartype)

    def test_01_same_existing_val_succeeds(self):
        name = "CMAKE_C_FLAGS" # use this because there are several other vars with the same prefix
        self.assertIn(name, self.original.keys())
        result = self._set_and_load({
            name: self.original[name].val,
        })
        self.assertEqual(result[name].val, self.original[name].val)
        self.assertEqual(result[name].vartype, self.original[name].vartype)
        for k, v in result.items():
            self.assertEqual(v.val, self.original[k].val)
            self.assertEqual(v.vartype, self.original[k].vartype)

    def test_10_set_multiple_val_succeeds(self):
        names = [
            "CMAKE_C_FLAGS",
            "CMAKE_C_COMPILER",
            "CMAKE_CXX_FLAGS",
            "CMAKE_CXX_COMPILER",
        ]
        varvalues = odict()
        for name in names:
            self.assertIn(name, self.original.keys())
            varvalues[name] = self.original[name].val + "asdads"
        result = self._set_and_load(varvalues)
        for name in names:
            self.assertNotEqual(result[name].val, self.original[name].val)
            self.assertEqual(result[name].vartype, self.original[name].vartype)
        # check no entries were added/removed
        self.assertEqual(len(result.keys()), len(self.original.keys()))
        self.assertEqual(list(sorted(result.keys())), list(sorted(self.original.keys())))
        for k, v in result.items():
            if k in names:
                self.assertNotEqual(v.val, self.original[k].val)
                self.assertEqual(v.vartype, self.original[k].vartype)
            else:
                self.assertEqual(v.val, self.original[k].val)
                self.assertEqual(v.vartype, self.original[k].vartype)

    def test_20_set_same_type_succeeds(self):
        names = [
            "CMAKE_C_FLAGS",
            "CMAKE_C_COMPILER",
            "CMAKE_CXX_FLAGS",
            "CMAKE_CXX_COMPILER",
        ]
        varvalues = odict()
        for name in names:
            self.assertIn(name, self.original.keys())
            var = self.original[name]
            varvalues[name + ":" + var.vartype] = var.val
        result = self._set_and_load(varvalues)
        for name in names:
            self.assertEqual(result[name].val, self.original[name].val)
            self.assertEqual(result[name].vartype, self.original[name].vartype)
        # check no entries were added/removed
        self.assertEqual(len(result.keys()), len(self.original.keys()))
        self.assertEqual(list(sorted(result.keys())), list(sorted(self.original.keys())))
        for k, v in result.items():
            self.assertEqual(v.val, self.original[k].val)
            self.assertEqual(v.vartype, self.original[k].vartype)

    @parameterized.expand([
        [
            "all_wrong", [
                ("CMAKE_C_FLAGS","FILEPATH"),
                ("CMAKE_C_COMPILER","STRING"),
                ("CMAKE_CXX_FLAGS","FILEPATH"),
                ("CMAKE_CXX_COMPILER","STRING"),
            ],
        ],
        [
            "one_wrong", [
                ("CMAKE_C_FLAGS","STRING"),
                ("CMAKE_C_COMPILER","STRING"),
                ("CMAKE_CXX_FLAGS","STRING"),
                ("CMAKE_CXX_COMPILER","FILEPATH"),
            ],
        ],
    ])
    def test_21_change_type_fails(self, casename, names):
        varvalues = odict()
        for name, vartype in names:
            self.assertIn(name, self.original.keys())
            varvalues[name+":"+vartype] = self.original[name].val
        with self.assertRaises(err.CannotChangeCacheVarType) as cm:
            c4cmake.setcachevars(self.dir, varvalues)


# -----------------------------------------------------------------------------

class Test05CMakeCache(ut.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _setup_cache()

    def test_00basic(self):
        c = c4cmake.CMakeCache(dstdir)
        self.assertGreater(len(c), 0)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'echo':
        print(sys.argv[2:])  # for test_invoke()
    else:
        ut.main()
