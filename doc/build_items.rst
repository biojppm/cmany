Build items
===========

(You can read this document with the command ``cmany help build_items``).

cmany creates its builds by combining build items. There are the following
classes of build items:

* systems: ``-s/--systems sys1[,sys2[,...]]``
* architectures: ``-a/--architectures arch1[,arch2[,...]]``
* compilers: ``-c/--compilers comp1[,comp2[,...]]``
* build types: ``-t/--build-types btype1[,btype2[,...]]``
* variants: ``-v/--variants var1[,var2[,...]]``

All of the arguments above accept a comma-separated list of items (but note
that no spaces should appear around the commmas). Repeated invokation of an
argument has the same effect. For example, ``-c g++,clang++`` is the same as
``-c g++ -c clang++``.

Any omitted argument will default to a list of a single item based on the
current system (for example, omitting ``-s`` in linux yields an implicit ``-s
linux`` whereas in windows yields an implicit ``-s windows``; or omitting
``-a`` in a 64 bit processor system yields an implicit ``-a x86_64``).

cmany will generate builds by combining every build item with every other
build item of different class. The resulting builds have a name of the form
``{system}-{architecture}-{compiler}-{build_type}[-{variant}]``.

Since the number of combinations grows very quickly and not every combination
will make sense, cmany has arguments to exclude certain combinations, either
by the resulting build name (with a regex) or by the names of the items that
a build would be composed of. Read more about it :doc:`here
</excluding_builds>`.

The following sections address each of these build items in more detail.


Per-item flags
--------------

To make a build item bring with it a set of compiler or cmake flags, use the
following syntax: ``'item_name: <flag_specs>....'`` instead of just
``item_name``. This will prompt cmany to use those flags whenever that build
item is used in a build. For example, you can add a flag only to a certain
build type::

  $ cmany b --build-types Release,'Debug: --cxxflags "-Wall"'

Note the use of the quotes; it is necessary to have the arguments correctly
parsed by the system.

See the :doc:`cmany help on flags </flags>` to discover what flags can be
used here. Note also that :doc:`exclusion flags </excluding_builds>` can also
be used as per-item flags.

When creating the flags for the build, the order is the following:

#. command-level flags
#. system flags
#. architecture flags
#. compiler flags
#. build type flags
#. variant flags

So command level flags come first and variant flags come last in the compiler
command line.


Inheriting per-item flags
^^^^^^^^^^^^^^^^^^^^^^^^^

To make a build item inherit all the flags in another build item, reference
the base item name prefixed with ``@``. The result is that the inheriting
item will have all the flags of the base item, plus its own flags inserted at
the point where the ``@`` reference occurs. :doc:`combination flags
</excluding_builds>` are not inherited. 

For example, note the ``@foo`` spec in the bar variant::

    $ cmany b -v none \
              -v 'foo: --defines SOME_DEFINE=32 --cxxflags "-Os"' \
              -v 'bar: @foo --defines SOME_DEFINE=16 -cxxflags "-O2"'

With this command, bar will be now consist of ``-D
SOME_DEFINE=32,SOME_DEFINE=16 -X "-Os","-O2"'``.

.. note::
   Order matters here: the place where the inheritance directive
   occurs is relevant. For example::

     $ cmany b -v none \
              -v 'foo: --defines SOME_DEFINE=32 --cxxflags "-Os"' \
              -v 'bar: --defines SOME_DEFINE=16 -cxxflags "-O2" @foo'

   will make bar consist instead of ``-D SOME_DEFINE=16,SOME_DEFINE=32 -X
   "-O2","-Os"``. So here ``SOME_DEFINE`` will have with a value of 16, as
   opposed to 32 which will be the value in the previous example. This happens
   because cmany will insert foo's options right in the place where ``@foo``
   appears.


Compilers
---------

cmany defaults to CMake's default compiler. To use different compilers,
use ``--compilers/-c``. Each argument given here must be an executable
compiler found in your path, or an absolute path to the compiler.

The following command chooses clang++ instead of CMake's default compiler::

    $ cmany b -c clang++

If the directory is initially empty, this will be the result::

    $ ls -1 build/*
    build/linux-x86_64-clang++3.9-Release/

Note that cmany will query the compiler for a name and a version. This is for
ensuring the use of different build trees for different versions of the same
compiler. The logic for extracting the compiler name/version may fail in some
cases, so open an issue if you see problems here.



Microsoft Visual Studio
^^^^^^^^^^^^^^^^^^^^^^^

Picking the Visual Studio version with CMake is harder than it should
be. :doc:`cmany tries to make this easier </vs>` to do. For example, this
will use Visual Studio 2015 **in the native architecture**::

    $ cmany b -c vs2015
    $ ls -1 build/*
    build/windows-x86_64-vs2015-Release/

as opposed to the option required by CMake, which would be ``-G "Visual
Studio 15 2017 Win64"``). So if cmany is running in a 32 bit system, then the
result of running the command above will be a 32 bit build instead::

    $ cmany b -c vs2015
    $ ls -1 build/*
    build/windows-x86-vs2015-Release/

An explicit request for the target architecture may be made by appending a
``_32`` or ``_64`` suffix. For example, if Visual Studio 2017 in 32 bit mode
is desired, then simply use ``vs2017_32``::

    $ cmany b -c vs2017_32
    $ ls -1 build/*
    build/windows-x86-vs2017-Release/

You can also choose the VS toolset to use in the compiler name. For example,
compile with the ``clang`` frontend (equivalent in this case to cmake's ``-T
v141_clang_c2`` option)::

    $ cmany b -c vs2017_clang
    $ ls -1 build/*
    build/windows-x86-vs2017_clang-Release/

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

Given the many VS versions, target architectures and toolsets, this creates
hundreds of possible aliases, so read :doc:`the complete documentation for
Visual Studio </vs>`.



Build types
-----------

cmany uses ``Release`` as the default build type. To set a different build
type use ``--build-types/-t``. The following command chooses a build type of
Debug instead of Release::

    $ cmany b -t Debug

If the directory is initially empty, this will be the result::

    $ ls -1 build/*
    build/linux-x86_64-g++6.1-Debug/

Note that the build naming scheme will cause build trees with different build
types to be placed in different directories. Apart from producing a better
organization of your builds, this saves you a full project rebuild when the
build type changes (and the cmake generator is not a multi-config generator
like MSVC).


Variants
--------

If you have read the :doc:`help on setting up </flags>` cmake cache variables,
preprocessor defines or compiler flags, you know that a direct invokation
like this::

  $ cmany b --defines FOO=bar ...more options

(ie, at the level of the cmany command) will cause these to apply to all the
builds produced by cmany. For setting up a bundle of cmake cache
variables, preprocessor defines or compiler flags to be combined with all
other build items, cmany offers **variants**.

A variant is a build item different from any other which uses a specific
combination of flags via ``--cmake-vars/-V``, ``--defines/-D``, ``--cxxflags/-X``,
``--cflags/-C``. Like all other build items, it will be combined with other
build items of different class. With the exception of the null variant,
variants will always have per-item flags.

The command option to setup a variant is ``--variant/-v`` and should be used
as follows: ``--variant 'variant_name: <variant_specs>'``. For example,
assume a vanilla build::

    $ cmany b

which will produce the following tree::

    $ ls -1 build
    build/linux-x86_64-clang3.9-Release/

If instead of this we want to produce two variants ``foo`` and ``bar`` with
specific defines and compiler flags, the following command should be used::

    $ cmany b --variant 'foo: --defines SOME_DEFINE=32 --cxxflags "-Os"' \
              --variant 'bar: --defines SOME_DEFINE=16 --cxxflags "-O2"'

To be clear, the ``foo`` variant will be compiled with the preprocessor symbol
named ``SOME_DEFINE`` defined to 32, and will use the ``-Os`` C++ compiler
flag. In turn, the ``bar`` variant will be compiled with the preprocessor
symbol named ``SOME_DEFINE`` defined to 16, and will use the ``-O2`` C++
compiler flag. So instead of the build above, we now get::

    $ ls -1 build
    build/linux-x86_64-clang3.9-Release-bar/
    build/linux-x86_64-clang3.9-Release-foo/

Variants will be combined, just like compilers or build types. So applying
the former two variants to the 9-build example above will result in 18
builds (3 compilers * 3 build types * 2 variants) ::

    $ cmany b -c clang++,g++,icpc -t Debug,Release,MinSizeRel \
              --variant 'foo: -D SOME_DEFINE=32 -X "-Os"' \
              --variant 'bar: -D SOME_DEFINE=16 -X "-O2"'
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

Note that ``--variant/-v`` accepts also comma-separated arguments::

    $ cmany b -c clang++,g++,icpc -t Debug,Release,MinSizeRel \
              --variant 'foo: -D SOME_DEFINE=32 -X "-Os"','bar: -D SOME_DEFINE=16 -X "-O2"'

Null variant
^^^^^^^^^^^^
cmany will combine only the given variant names. Notice above that the
basic (variant-less) build ``linux-x86_64-clang3.9-Debug`` is not there. 
To retain the basic build without a variant suffix use the special name ``none``::

    $ cmany b -v none \
              -v 'foo: -D SOME_DEFINE=32 -X "-Os"' \
              -v 'bar: -D SOME_DEFINE=16 -X "-O2"'
    $ ls -1 build
    build/linux-x86_64-clang3.9-Release/
    build/linux-x86_64-clang3.9-Release-bar/
    build/linux-x86_64-clang3.9-Release-foo/

You can add flags to the none variant as well, and use inheritance at will.



Systems
-------


Architectures
-------------

Or if you want to invoke gcc both in 32 and 64 bit mode while in a 64 bit
system::

  $ cmany b --architectures x86_64,'x86: --cxxflags "-m32"'

(In practice, cmany already does exactly this for you when you select the x86
architecture: when cmany is given ``cmany b -a x86_64,x86`` the ``-m32`` flag
is implicitly added by cmake when it is run in a x86_64 system. But hopefully
you get the point.)

