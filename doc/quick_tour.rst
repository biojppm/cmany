Quick tour
==========


Getting help
------------

To get a list of available commands and help topics::

    $ cmany help

To get help on a particular command or topic (eg, ``build``), any
of the following can be used, and they are all equivalent::

    $ cmany help build
    $ cmany h build             # help has an alias: h 
    $ cmany build -h
    $ cmany build --help


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
type. The ``build`` command has an alias of ``b``. So the following command is
exactly the same as ``cmany build .``::

    $ cmany b


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

To set the build types use ``-t`` or ``--build-types``. The following command
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

To choose the compiler use ``-c`` or ``--compilers``. The following command
chooses clang++ instead of CMake's default compiler. If the directory is
initially empty, this will be the result::

    $ cmany b -t Debug
    $ ls -1 build/*
    build/linux-x86_64-clang3.9-Debug/
        

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

You don't have to use cmany's default build/install dirs. The following
command will use ``foo`` for building and ``bar`` for installing::

    $ cmany i -c clang++,g++ --build-dir foo --install-dir bar path/to/proj/dir

    $ ls -1 foo/ bar/
    bar/linux-x86_64-clang3.9-Release/
    bar/linux-x86_64-gcc6.1-Release/
    bar/linux-x86_64-icc16.1-Release/
    foo/linux-x86_64-clang3.9-Release/
    foo/linux-x86_64-gcc6.1-Release/
    foo/linux-x86_64-icc16.1-Release/

Note that ``foo`` and ``bar`` will still be placed under the current working
directory.


Fine-tuning the build parameters
--------------------------------

Being able to combine compilers and build types is nice, but it's not
enough. For sure, there is also the need for setting cmake cache variables,
preprocessor and compiler flags. This section is an intro on how to achieve
this. It is also a stepping stone for more advanced usage, such as
variants and per-combination-parameter options.

Note that all of the options below apply across the board to all the
individual builds produced by the command. For example, this will add
``-Wall`` to all of the 9 builds in the example above::

    $ cmany b -c clang++,g++,icpc -t Debug,Release,MinSizeRel -X "--Wall"

If you want something more specific, it's cool! One of the main motivations
of cmany is being able to easily create variations in which the options below
apply only to certain builds. If you want to do this, you can either a) use
**variants** or b) specify those parameters to be specific to the OS,
architecture, compiler, or build configuration (WIP). Let's start first by
showing how to set these parameters.

CMake cache variables
^^^^^^^^^^^^^^^^^^^^^

You can set cmake cache variables using ``-V``/``--vars``. For example, the
following command will be the same as if ``cmake -DCMAKE_VERBOSE_MAKEFILES=1
-DPROJECT_FOO=BAR .`` followed by ``cmake --build`` was used::

    $ cmany b -V CMAKE_VERBOSE_MAKEFILES=1,PROJECT_FOO=BAR

Note the use of the comma to separate the variables. This is for consistency
with the rest of the cmany options, namely (for example) those selecting,
compilers or build types. You can also use separate invocations::

    $ cmany b -V CMAKE_VERBOSE_MAKEFILES=1 -V PROJECT_FOO=BAR

which will have the same result as above.

Note that these cmake cache variables will be used across the board in all
the individual builds produced by the cmany command.

Preprocessor macros
^^^^^^^^^^^^^^^^^^^

To add preprocessor macros, use the option ``-D``/``--defines``::

    $ cmany b -D MY_MACRO=1,FOO=BAR

The command above has the same meaning as if ``cmake -D
CMAKE_CXX_FLAGS="-DMY_MACRO=1 -DFOO=BAR"`` followed by ``cmake --build`` was used.

These macros will be used across the board in all the individual builds
produced by the cmany command.

C++ compiler flags
^^^^^^^^^^^^^^^^^^

To add C++ compiler flags, use the option ``-X``/``--cxxflags``. To prevent
these flags being interpreted as cmany command options, use quotes or single
quotes::

    $ cmany b -X "--Wall","-O3"      # add -Wall -O3 to all builds

These flags will be used across the board in all the individual builds
produced by the cmany command.

C compiler flags
^^^^^^^^^^^^^^^^

To add C compiler flags, use the option ``-C``/``--cflags``. As with C++
flags, use quotes to escape::

    $ cmany b -C "--Wall","-O3"

These flags will be used across the board in all the individual builds
produced by the cmany command.



Build variants
--------------

cmany has **variants** for setting up per-build parameters. A variant is a
build different from any other, and uses a combination of the options of the
previous section (``--vars``, ``--defines``, ``--cxxflags``,
``--cflags``).

For example, we may want to compile ``linux-x86_64-clang3.9-Release`` with
exceptions enabled and disabled. So in fact we would have
``linux-x86_64-clang3.9-Release`` and
``linux-x86_64-clang3.9-Release-no_exceptions``.

The command option to setup a variant is as follows: ``-v 'variant_name:
<variant_specs>'``. For example, the following command will produce two
variants, one named foo, and another named bar::

    $ cmany b -v 'foo: -D FOO_FEATURE=32 -X "-Os"','bar: -D BAR_FEATURE=16 -X "-O2"'

To be clear, the ``foo`` variant will be compiled with a preprocessor symbol named
``FOO_FEATURE`` defined to 32, and will use the ``-Os`` C++ compiler flag. In
turn, the ``bar`` var will be compiled with a preprocessor symbol named
``BAR_FEATURE`` defined to 16, and will use the ``-O2`` C++ compiler
flag. This will produce 2 builds::

    $ ls -1 build
    build/linux-x86_64-clang3.9-Release-bar/
    build/linux-x86_64-clang3.9-Release-foo/

Like compilers or build types, variants will be combined. So applying the
former two variants to the 9-build example above would result in 18 builds ::

    $ cmany b -c clang++,g++,icpc -t Debug,Release,MinSizeRel \
     -v 'foo: -D FOO_FEATURE=32 -X "-Os"','bar: -D BAR_FEATURE=16 -X "-O2"'

    $ ls -1 build/
    build/linux-x86_64-clang3.9-Debug-bar/
    build/linux-x86_64-clang3.9-Debug-foo/
    build/linux-x86_64-clang3.9-MinSizeRel-bar/
    build/linux-x86_64-clang3.9-MinSizeRel-foo/
    build/linux-x86_64-clang3.9-Release-bar/
    build/linux-x86_64-clang3.9-Release-foo/
    build/linux-x86_64-gcc6.1-Debug-bar/
    build/linux-x86_64-gcc6.1-Debug-foo/
    build/linux-x86_64-gcc6.1-MinSizeRel-bar/
    build/linux-x86_64-gcc6.1-MinSizeRel-foo/
    build/linux-x86_64-gcc6.1-Release-bar/
    build/linux-x86_64-gcc6.1-Release-foo/
    build/linux-x86_64-icc16.1-Debug-bar/
    build/linux-x86_64-icc16.1-Debug-foo/
    build/linux-x86_64-icc16.1-MinSizeRel-bar/
    build/linux-x86_64-icc16.1-MinSizeRel-foo/
    build/linux-x86_64-icc16.1-Release-bar/
    build/linux-x86_64-icc16.1-Release-foo/

