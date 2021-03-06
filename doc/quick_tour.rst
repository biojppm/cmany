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

Note that this text is also available as a help topic. You can read it with
the help command::

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
compiler. cmany's default build type is (explicitly set to) ``Release``. As an
example, using g++ 6.1 in Linux x86_64, the result of the command above will
be this::

    $ tree -fi -L 2
    build/
    build/linux-x86_64-g++6.1-Release/
    CMakeLists.txt
    main.cpp

    $ ls build/*/CMakeCache.txt
    build/linux-x86_64-g++6.1-Release/CMakeCache.txt

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
    install/linux-x86_64-g++6.1-Release/
    install/linux-x86_64-g++6.1-Release/bin/
    install/linux-x86_64-g++6.1-Release/bin/hello


Choosing the build type
-----------------------

cmany uses Release as the default build type. To set a different build type
use ``--build-types/-t``. The following command chooses a build type of Debug
instead of Release::

    $ cmany b -t Debug

If the directory is initially empty, this will be the result::

    $ ls -1 build/*
    build/linux-x86_64-g++6.1-Debug/

Note that the build naming scheme will cause build trees with different build
types to be placed in different directories. Apart from producing a better
organization of your builds, this saves you a full project rebuild when the
build type changes (and the cmake generator is not a multi-config generator
like MSVC).


Choosing the compiler
---------------------

cmany defaults to CMake's default compiler. To use different compilers,
use ``--compilers/-c``. Each argument given here must be an executable
compiler found in your path, or an absolute path to the compiler.

The following command chooses clang++ instead of CMake's default compiler::

    $ cmany b -c clang++

If the directory is initially empty, this will be the result::

    $ ls -1 build/*
    build/linux-x86_64-clang++3.9-Release/

:ref:`Read more here <Compilers>`.


Choosing build/install directories
----------------------------------

By default, cmany creates the build trees nested under a directory ``build``
which is created as a sibling of the ``CMakeLists.txt`` project file. Similarly,
the install trees are nested under the ``install`` directory. However, you
don't have to use these defaults. The following command will use ``foo`` for
building and ``bar`` for installing::

    $ cmany i -c clang++,g++ --build-dir foo --install-dir bar

    $ ls -1 foo/ bar/
    bar/linux-x86_64-clang++3.9-Release/
    bar/linux-x86_64-g++6.1-Release/
    bar/linux-x86_64-icpc16.1-Release/
    foo/linux-x86_64-clang++3.9-Release/
    foo/linux-x86_64-g++6.1-Release/
    foo/linux-x86_64-icpc16.1-Release/

Note that ``foo`` and ``bar`` will still be placed under the current working
directory, since they are given as relative paths. cmany also accepts
absolute paths here.


Building many trees at once
---------------------------

The commands shown up to this point were only fancy wrappers for CMake. Since
defaults were being used, or single arguments were given, the result for each
command was a single build tree. But as its name attests to, cmany will build
many trees at once by combining the build items. For example, to build
both ``Debug`` and ``Release`` build types while using defaults for the
remaining parameters, you can do the following (resulting in 2 build trees)::

    $ cmany b -t Debug,Release
    $ ls -1 build/
    build/linux-x86_64-g++6.1-Debug/
    build/linux-x86_64-g++6.1-Release/

You can also do this for the compilers (2 build trees)::

    $ cmany b -c clang++,g++
    $ ls -1 build/
    build/linux-x86_64-clang++3.9-Release/
    build/linux-x86_64-g++6.1-Release/

And you can also combine all of them (4 build trees)::

    $ cmany b -c clang++,g++ -t Debug,Release
    $ ls -1 build/
    build/linux-x86_64-clang++3.9-Debug/
    build/linux-x86_64-clang++3.9-Release/
    build/linux-x86_64-g++6.1-Debug/
    build/linux-x86_64-g++6.1-Release/

Another example -- build using clang++,g++,icpc for Debug,Release,MinSizeRel build types
(9 build trees)::

    $ cmany b -c clang++,g++,icpc -t Debug,Release,MinSizeRel
    $ ls -1 build/
    build/linux-x86_64-clang++3.9-Debug/
    build/linux-x86_64-clang++3.9-MinSizeRel/
    build/linux-x86_64-clang++3.9-Release/
    build/linux-x86_64-g++6.1-Debug/
    build/linux-x86_64-g++6.1-MinSizeRel/
    build/linux-x86_64-g++6.1-Release/
    build/linux-x86_64-icpc16.1-Debug/
    build/linux-x86_64-icpc16.1-MinSizeRel/
    build/linux-x86_64-icpc16.1-Release/

The items that can be combined by cmany are called **build items**. cmany
:doc:`has the following classes of build items </build_items>`:

* systems: ``-s/--systems sys1[,sys2[,...]]``
* architectures (``-a/--architectures arch1[,arch2[,...]]``
* compilers (``-c/--compilers comp1[,comp2[,...]]``
* build types (``-t/--build-types btype1[,btype2[,...]]``
* variants (``-v/--variants var1[,var2[,...]]``

All of the arguments above accept a comma-separated list of items. Any
omitted argument will default to a list of a single item based on the current
system (for example, omitting ``-s`` in linux yields an implicit ``-s linux``
whereas in windows yields an implicit ``-s windows``; or omitting ``-a`` in a
64 bit processor system yields an implicit ``-a x86_64``).

cmany will generate builds by combining every build item with every other
build item of different class. The resulting build has a name of the form
``{system}-{architecture}-{compiler}-{build_type}[-{variant}]``.

A variant is a build item which brings with it a collection of flags. This
allows for easy combination of these flags with other build items. But note
that every build item can bring specific flags with it.

Since the number of build item combinations grows very quickly and not every
combination will make sense, cmany has arguments to exclude certain
combinations, either by the resulting build name (with a regex) or by the
names of the items that a build would be composed of. Read more about it
:doc:`here </excluding_builds>`.


Using flags
-----------

(:doc:`Full docs for flags here </flags>`).

You can set cmake cache variables using ``--cmake-vars/-V``. For example, the
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

Using flags per build item is easy. Instead of specifying the flags at the
command level as above, specify them at build item. For example::

    $ cmany b --variant 'foo: --defines SOME_DEFINE=32 --cxxflags "-Os"' \
              --variant 'bar: --defines SOME_DEFINE=16 --cxxflags "-O2"'

To be clear, the ``foo`` variant will be compiled with the preprocessor
symbol named ``SOME_DEFINE`` defined to 32, and will use the ``-Os`` C++
compiler flag. In turn, the ``bar`` variant will be compiled with the
preprocessor symbol named ``SOME_DEFINE`` defined to 16, and will use the
``-O2`` C++ compiler flag. So instead of the build above, we now get::

    $ ls -1 build
    build/linux-x86_64-clang++3.9-Release-bar/
    build/linux-x86_64-clang++3.9-Release-foo/

Note above the additional ``-foo`` and ``-bar`` suffixes to denote the
originating variant.

You can make build items inherit the flags from other build items: add a
``@`` reference to the variant you want to inherit from. For example::

    $ cmany b --variant 'foo: --defines SOME_DEFINE=32 --cxxflags "-Os"' \
              --variant 'bar: @foo --defines SOME_DEFINE=16 --cxxflags "-O2"'

This will result in the ``bar`` variant having its flags specifications as
``--defines SOME_DEFINE=32 --cxxflags "-Os" --defines
SOME_DEFINE=16 --cxxflags "-O2"``.


Cross-compiling
---------------

`Cross compilation with cmake
<https://cmake.org/Wiki/CMake_Cross_Compiling>`_ requires passing a
`toolchain file
<https://cmake.org/cmake/help/v3.0/manual/cmake-toolchains.7.html>`_. cmany
has the ``--toolchain`` option for this. This is more likely to be used as a
flag of the system or architecture build type.



Building dependencies
---------------------

cmany offers the argument ``--deps path/to/extern/CMakeLists.txt`` to enable
building another CMake project which builds and installs the dependencies of
the current project. When ``--deps`` is given, the external project is built
for each configuration, and installed in the configuration's build
directory. Use ``--deps-prefix`` to specify a different install directory for
the external project. :doc:`Read more here </dependencies>`.


Argument reuse
--------------

Due to the way that compilation flags are accepted, the full form of a cmany
command can become big. To save you from retyping the command, you can set
the ``CMANY_ARGS`` environment variable to reuse arguments to cmany. As an
experimental (and buggy) feature, you can also permanently store these
options in a ``cmany.yml`` project file, which should be placed side by side
with the project ``CMakeLists.txt``. You can :doc:`find more about this here
</reusing_arguments>`.


Exporting build configurations
------------------------------

cmany has the command ``export_vs``, which exports the build configurations
to Visual Studio through the file ``CMakeSettings.json`` (placed side by side
with the project ``CMakeLists.txt``). Read `this MS blog post
<https://blogs.msdn.microsoft.com/vcblog/2016/10/05/cmake-support-in-visual-studio/>`_
to discover how to use the generated file.

For code-intelligence tools requiring knowledge of the compilation commands
(for example, rtags, and many other tools used with emacs), cmany offers also
the argument ``-E/--export-compile``. This argument will instruct cmake to
generate the file ``compile_commands.json`` (placed in each build tree).
