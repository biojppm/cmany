Quick tour
==========


Getting help
------------

To get a list of available commands and help topics::

    $ cmany help

To get help on a particular command (eg, ``build``) or topic (eg, ``quick_tour``), any
of the following can be used, and they are all equivalent::

    $ cmany help build
    $ cmany h build             # help has an alias: h 
    $ cmany build -h
    $ cmany build --help

This text is also a help topic. You can read it with the help
command::

    $ cmany h quick_tour

Build
-----

Consider a directory initially with this layout::

    $ ls -1
    CMakeLists.txt
    main.cpp

The following command invokes CMake to configure and build this project::

    $ cmany build .

Like with CMake, this will look for the CMakeLists.txt file at the given path
(``.``) and place the build tree at the current working directory. If the
path is omitted, CMakeLists.txt is assumed to be on the current working dir.
Also, the ``build`` command has an alias of ``b``. So the following command is
exactly the same as ``cmany build .``::

    $ cmany b

When no compiler is specified, cmany chooses CMake's default
compiler. cmany's default build type is (explicitly set to) Release. As an
example, using g++ 6.1 in Linux x86_64, the result of the command above will
be this::

    $ tree -fi -L 2
    build/
    build/linux-x86_64-gcc6.1-Release/
    CMakeLists.txt
    main.cpp

    $ ls build/*/CMakeCache.txt
    build/linux-x86_64-gcc6.1-Release/CMakeCache.txt

Note that unlike CMake, cmany will not place the resulting build tree
directly at the current working directory: it will instead nest it under
``./build``. Each build tree name is made unique by combining the names of
the operating system, architecture, compiler+version and the CMake build
type.


Configure
---------

It was said above that the ``cmany build`` command will also configure. In
fact, cmany will detect when a configure step is needed. But you can just use
``cmany configure`` if that's only what you want to do::

    $ cmany configure

Same as above: ``c`` is an alias to ``configure``::

    $ cmany c


Install
-------

The ``cmany install`` command does what it says, and will also ``configure``
and ``build`` if needed. ``i`` is an alias to ``install``::

    $ cmany i

The install root defaults to ``./install``. So assuming the project creates
a single executable named ``hello``, the following will result::

    $ ls -1
    CMakeLists.txt
    build/
    install/
    main.cpp

    $ tree -fi install
    install/
    install/linux-x86_64-gcc6.1-Release/
    install/linux-x86_64-gcc6.1-Release/bin/
    install/linux-x86_64-gcc6.1-Release/bin/hello


Choosing the build type
-----------------------

To set the build types use ``--build-types/-t``. The following command
chooses a build type of Debug instead of Release. If the directory is
initially empty, this will be the result::

    $ cmany b -t Debug
    $ ls -1 build/*
    build/linux-x86_64-gcc6.1-Debug/

Note that the build naming scheme will cause build trees with different build
types to be placed in different directories. Apart from producing a better
organization of your builds, this saves you a full project rebuild when the
build type changes (and the cmake generator is not a multi-config generator
like MSVC).


Choosing the compiler
---------------------

To choose the compiler use ``--compilers/-c``. The following command
chooses clang++ instead of CMake's default compiler. If the directory is
initially empty, this will be the result::

    $ cmany b -c clang++
    $ ls -1 build/*
    build/linux-x86_64-clang3.9-Release/

The given compiler should be found in the path.

Microsoft Visual Studio
^^^^^^^^^^^^^^^^^^^^^^^

cmany makes it easier than CMake to :doc:`specify which Visual Studio
version </vs>` to use. For example, this will use Visual Studio 2015 **in the
native architecture**::

    $ cmany b -c vs2015
    $ ls -1 build/*
    build/windows-x86_64-vs2015-Release/

as opposed to the option required by CMake, which would be ``-G "Visual
Studio 15 2017 Win64"``). Significantly, this will use the native
architecture (this is a behaviour slightly different from CMake). So if cmany
is running in a 32 bit system, then the result of running the command above
would be a 32 bit build instead::

    $ cmany b -c vs2015
    $ ls -1 build/*
    build/windows-x86-vs2015-Release/

An explicit request for the target architecture may be made by appending a
``_32`` or ``_64`` suffix. For example, if Visual Studio 2017 in 32 bit mode
is desired, then simply use ``vs2017_32``::

    $ cmany b -c vs2017_32
    $ ls -1 build/*
    build/windows-x86-vs2017-Release/

cmany allows you to create any valid combination of the Visual Studio project
versions (from vs2017 to vs2005), target architectures (32, 64, arm, ia64)
and toolsets (from v141 to v80, with clang_c2 and xp variants). The general
form for the cmany VS specification alias is::

    <vs_project_version>[_<vs_platform_version>][_<vs_toolset_version>]

Note that the order must be exactly as given. Note also that the platform
version or the toolset version can be omitted, in which case a sensible
default will be used:

   * if the platform is omitted, then the current platform will be used
   * if the toolset is omitted, then the toolset of the given project version
     will be used.

This creates hundreds of possible aliases, so read :doc:`the complete
documentation for Visual Studio </vs>`.


Building many trees at once
---------------------------

The commands shown up to this point were only fancy, practical wrappers for
CMake. Since defaults were being used, or single arguments were given, the
result for each command was a single build tree. But as its name attests to,
cmany will build many trees at once by combining the build parameters. For
example, to build both Debug and Release build types while using defaults for
the remaining parameters, you can do the following (resulting in 2 build
trees)::

    $ cmany b -t Debug,Release
    $ ls -1 build/
    build/linux-x86_64-gcc6.1-Debug/
    build/linux-x86_64-gcc6.1-Release/

You can also do this for the compilers (2 build trees)::

    $ cmany b -c clang++,g++
    $ ls -1 build/
    build/linux-x86_64-clang3.9-Release/
    build/linux-x86_64-gcc6.1-Release/

And you can also combine all of them (4 build trees)::

    $ cmany b -c clang++,g++ -t Debug,Release
    $ ls -1 build/
    build/linux-x86_64-clang3.9-Debug/
    build/linux-x86_64-clang3.9-Release/
    build/linux-x86_64-gcc6.1-Debug/
    build/linux-x86_64-gcc6.1-Release/

Another example -- build using clang++,g++,icpc for Debug,Release,MinSizeRel build types
(9 build trees)::

    $ cmany b -c clang++,g++,icpc -t Debug,Release,MinSizeRel
    $ ls -1 build/
    build/linux-x86_64-clang3.9-Debug/
    build/linux-x86_64-clang3.9-MinSizeRel/
    build/linux-x86_64-clang3.9-Release/
    build/linux-x86_64-gcc6.1-Debug/
    build/linux-x86_64-gcc6.1-MinSizeRel/
    build/linux-x86_64-gcc6.1-Release/
    build/linux-x86_64-icc16.1-Debug/
    build/linux-x86_64-icc16.1-MinSizeRel/
    build/linux-x86_64-icc16.1-Release/


Choosing build/install directories
----------------------------------

By default, cmany creates the build trees nested under a directory ``build``
which is created as a sibling of the ``CMakeLists.txt`` project file. Similarly,
the install trees are nested under the ``install`` directory. However, you
don't have to use these defaults. The following command will use ``foo`` for
building and ``bar`` for installing::

    $ cmany i -c clang++,g++ --build-dir foo --install-dir bar

    $ ls -1 foo/ bar/
    bar/linux-x86_64-clang3.9-Release/
    bar/linux-x86_64-gcc6.1-Release/
    bar/linux-x86_64-icc16.1-Release/
    foo/linux-x86_64-clang3.9-Release/
    foo/linux-x86_64-gcc6.1-Release/
    foo/linux-x86_64-icc16.1-Release/

Note that ``foo`` and ``bar`` will still be placed under the current working
directory.


Using flags/defines/cache vars
------------------------------

(:doc:`Full docs for flags here </flags>`).

You can set cmake cache variables using ``--vars/-V``. For example, the
following command will be the same as if ``cmake -DCMAKE_VERBOSE_MAKEFILES=1
-DPROJECT_SOME_DEFINE=SOME_DEFINE= .`` followed by ``cmake --build`` was
used::

    $ cmany b -V CMAKE_VERBOSE_MAKEFILES=1,PROJECT_SOME_DEFINE=SOME_DEFINE=

To add preprocessor macros, use the option ``--defines/-D``::

    $ cmany b -D MY_MACRO=1,FOO=bar,SOME_DEFINE

The command above has the same meaning as if ``cmake -D
CMAKE_CXX_FLAGS="-DMY_MACRO=1 -DFOO=bar -DSOME_DEFINE"`` followed by ``cmake
--build`` was used.

To add C++ compiler flags, use the command line option
``--cxxflags/-X``. To prevent these flags being interpreted as cmany
command options, use quotes or single quotes::

    $ cmany b -X "--Wall","-O3"      # add -Wall -O3 to all builds

To add C compiler flags, use the option ``--cflags/-C``. As with C++
flags, use quotes to escape::

    $ cmany b -C "--Wall","-O3"

The cmake cache variables, preprocessor defines and compiler flags specified
this way will be used across the board in all the individual builds produced
by the cmany command. For applying these only to certain builds, you can use
build **variants**, introduced next.

Build variants
--------------

(:doc:`Full docs for variants here </variants>`).

cmany has **variants** for setting up per-build parameters. A variant is a
build different from any other which uses a specific combination of the
options of the previous section (``--vars/-V``, ``--defines/-D``,
``--cxxflags/-X``, ``--cflags/-C``). The command option to setup a variant is
``--variant/-v`` and should be used as follows: ``--variant 'variant_name:
<flag_specs>'``. For example, assume a vanilla build::

    $ cmany b

which will produce the following tree::

    $ ls -1 build
    build/linux-x86_64-clang3.9-Release/

If want instead to produce two variants ``foo`` and ``bar`` with some
specific defines and compiler flags, the following command should be used::

    $ cmany b --variant 'foo: --defines SOME_DEFINE=32 --cxxflags "-Os"' \
              --variant 'bar: --defines SOME_DEFINE=16 --cxxflags "-O2"'

To be clear, the ``foo`` variant will be compiled with the preprocessor
symbol named ``SOME_DEFINE`` defined to 32, and will use the ``-Os`` C++
compiler flag. In turn, the ``bar`` variant will be compiled with the
preprocessor symbol named ``SOME_DEFINE`` defined to 16, and will use the
``-O2`` C++ compiler flag. So instead of the build above, we now get::

    $ ls -1 build
    build/linux-x86_64-clang3.9-Release-bar/
    build/linux-x86_64-clang3.9-Release-foo/

Note above the additional ``-foo`` and ``-bar`` suffixes to denote the
originating variant.

You can also make variants inherit from other variants, as well as having a
null variant. Read more about this in the :doc:`variants` document.

Per-parameter flags
-------------------

The pattern ``item_name: <flag_specs>`` which is used for specifying the
flags to use in :doc:`a variant </variants>` can also be used for making a
bundle of flags be used whenever a certain build combination parameter is
used. In other words, the variant mechanism also applies to the following
parameters:

 * operating system (``--systems/-s``)
 * architecture (``--architectures/-a``)
 * compiler (``--compilers/-c``)
 * build type (``--build-types/-t``)

Some examples follow.

For example, to associate specific flags to an operating system in order to
used a toolchain, you can simply do::

  $ cmany b --systems linux,'android: --vars CMAKE_TOOLCHAIN=toolchain.cmake'

This will build linux with default settings, and will make the android build
use a cmake toolchain file.

Or if you want to invoke gcc in both in 32 and 64 bit mode while in a 64 bit
system::

  $ cmany b --architecture x86_64,'x86: --cxxflags "-m32"'

Or if you want to add a special define only for one compiler::

  $ cmany b --compilers g++,'clang++: --defines FOO=bar"'

Or you can add a flag only to a certain build type::

  $ cmany b --build-types Release,'Debug: --cxxflags "-Wall"'

Again, all of the :doc:`flag directives </flags>` can be used inside the
``item_name: <flags>`` pattern.

Cross-compiling
---------------

Cross compilation with cmany is easy: just use per-parameter flags for your
target operating system, as described in the previous section.
