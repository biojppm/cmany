
.. image:: https://travis-ci.org/biojppm/cmany.svg?branch=master
    :target: https://travis-ci.org/biojppm/cmany
.. image:: https://ci.appveyor.com/api/projects/status/github/biojppm/cmany?branch=master&svg=true
    :target: https://ci.appveyor.com/project/biojppm/cmany

cmany
=====

Easily batch-build cmake projects!

cmany is a command line tool and Python3 module to easily build several
variations of a CMake C/C++ project. It combines different compilers, cmake
build types, processor architectures (WIP), operating systems (also WIP), or
compilation flags (WIP). cmany works and is continuously tested in Linux, Mac
OS X and Windows.

For example, to configure and build a project using clang++ and g++
in both Debug and Release::

    $ cmany build -c clang++,g++ -t Debug,Release path/to/CMakeLists.txt

The command above will result in four different build trees, placed by default
under a ``build`` folder which is under the current folder::

    $ tree -fi -L 2
    build
    build/linux-x86_64-clang3.9-Debug
    build/linux-x86_64-clang3.9-Release
    build/linux-x86_64-gcc6.1-Debug
    build/linux-x86_64-gcc6.1-Release


Features
--------

* Saves the tedious work of dealing with many build trees by hand.
* Useful for build comparisons.
* Useful for cross-compiler validation.
* Avoids a full rebuild when the build type is changed. Although this feature
  already exists in multi-configuration cmake generators like Visual
  Studio, it is missing from mono-configuration generators like Unix
  Makefiles.
* ... TODO


Basic usage examples
--------------------

Consider a directory with this layout::

    $ ls -1
    CMakeLists.txt
    main.cpp

The following command invokes CMake to configure this project::

    $ cmany configure .

When no compiler is specified, cmany chooses the compiler that CMake would
default to (this is done by calling ``cmake --system-information``). cmany's
default build type is Release, and it explicitly sets the build type even
when it is not given. As an example, using g++ 6.1 in Linux x86_64, the
result of the command above will be this::

    $ tree -fi -L 2
    build/
    build/linux-x86_64-gcc6.1-release/
    CMakeLists.txt
    main.cpp

    $ ls build/*/CMakeCache.txt
    build/linux-x86_64-gcc6.1-release/CMakeCache.txt

The command-line behaviour of cmany is similar to that of CMake except
that the resulting build tree is not placed directly at the current
directory, but will instead be nested under ``./build``. To make it
unique, the name for each build tree will be obtained from combining
the names of the operating system, architecture, compiler+version and
the CMake build type. Like with CMake, omitting the path to the
project dir will cause searching for CMakeLists.txt on the current
dir. Also, the configure command has an alias of ``c``. So the following
has the same result as above::

    $ cmany c

The ``cmany build`` command will configure AND build at once as if per
``cmake --build``. This will invoke ``cmany configure`` if necessary::

    $ cmany build

Same as above: ``b`` is an alias to ``build``::

    $ cmany b

The ``cmany install`` command does the same as above, and additionally
installs. That is, configure AND build AND install. ``i`` is an alias to
``install``::

    $ cmany i

The install root defaults to ``./install``. So assuming the project creates
an executable named ``hello``, the following will result::

    $ ls -1
    CMakeLists.txt
    build/
    install/
    main.cpp
    $ tree -fi install
    install/
    install/linux-x86_64-gcc6.1-release/
    install/linux-x86_64-gcc6.1-release/bin/
    install/linux-x86_64-gcc6.1-release/bin/hello

To set the build types use ``-t`` or ``--build-types``. The following command
chooses a build type of Debug instead of Release. If the directory is
initially empty, this will be the result::

    $ cmany b -t Debug
    $ ls -1 build/*
    build/linux-x86_64-gcc6.1-debug/

The commands shown up to this point were only fancy wrappers for CMake. Since
defaults were being used, or single arguments were given, the result was a
single build tree. But as its name attests to, cmany will build many trees at
once by combining the build parameters. For example, to build both Debug and
Release build types while using defaults for the remaining parameters, you
can do the following (resulting in 2 build trees)::

    $ cmany b -t Debug,Release
    $ ls -1 build/*
    build/linux-x86_64-gcc6.1-debug/
    build/linux-x86_64-gcc6.1-release/

To set the compilers use ``-c`` or ``--compilers``. For example, build
using both clang++ and g++; with the default build type (2 build trees)::

    $ cmany b -c clang++,g++
    $ ls -1 build/
    build/linux-x86_64-clang3.9-release/
    build/linux-x86_64-gcc6.1-release/

Build using both clang++,g++ for Debug,Release build types (4 build trees)::

    $ cmany b -c clang++,g++ -t Debug,Release
    $ ls -1 build/
    build/linux-x86_64-clang3.9-debug/
    build/linux-x86_64-clang3.9-release/
    build/linux-x86_64-gcc6.1-debug/
    build/linux-x86_64-gcc6.1-release/

Build using clang++,g++,icpc for Debug,Release,MinSizeRel build types
(9 build trees)::

    $ cmany b -c clang++,g++,icpc -t Debug,Release,MinSizeRel
    $ ls -1 build/
    build/linux-x86_64-clang3.9-debug/
    build/linux-x86_64-clang3.9-minsizerel/
    build/linux-x86_64-clang3.9-release/
    build/linux-x86_64-gcc6.1-debug/
    build/linux-x86_64-gcc6.1-minsizerel/
    build/linux-x86_64-gcc6.1-release/
    build/linux-x86_64-icc16.1-debug/
    build/linux-x86_64-icc16.1-minsizerel/
    build/linux-x86_64-icc16.1-release/

To get a list of available commands and help topics::

    $ cmany help

To get help on a particular command or topic (eg, ``build``), any
of the following can be used::

    $ cmany help build
    $ cmany build -h
    $ cmany build --help


License
-------

This project is licensed under the MIT license.

Status
------

This project is a pre-alpha under development.

Installation
------------

To install from source using Pip::

    git clone https://github.com/biojppm/cmany
    cd cmany
    pip3 install .

Contribute
----------

Send pull requests to `<https://github.com/biojppm/cmany/pulls>`.

Support
-------

Send bug reports to `<https://github.com/biojppm/cmany/issues>`.

