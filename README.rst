cmany
=====

Easily batch-build cmake projects!

cmany is a command line tool and Python3 module to easily build
several variations of a CMake C/C++ project. These variations
consist in combining different compilers, cmake build types, processor
architectures (WIP), operating systems (also WIP), or compilation flags (WIP).

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

* Saves the tedious work of dealing with several build trees by hand.
* Useful for build comparisons.
* Avoids a full rebuild when the build type is changed. Although this feature already exists in multi-configuration cmake generators such as Visual Studio, it is missing from mono-configuration generators like Unix Makefiles.
* ... TODO


Basic usage examples
--------------------

Consider a directory with the following CMake project::

    $ tree -fi -L 2
    ./CMakeLists.txt
    ./main.cpp

The following command invokes CMake to configure this project::

    $ cmany configure .

As an example, using g++ 6.1 in Linux x86_64, the result of the command above
will be this::

    $ tree -fi -L 2
    ./build
    ./build/linux-x86_64-gcc6.1-release
    ./CMakeLists.txt
    ./main.cpp
     
    $ ls build/*/CMakeCache.txt
    ./build/linux-x86_64-gcc6.1-release/CMakeCache.txt

The command-line behaviour of cmany is similar to that of CMake
except that the resulting build tree is not placed directly at the current
directory, but will instead be nested under ``./build``,
which is created if it doesn't exist. To make it unique, the name
for the build tree will be obtained from combining the names of the
operating system, architecture, compiler+version and the CMake build type.
Like with CMake, omitting the path to the project dir will cause
searching for CMakeLists.txt on the current dir.
The configure command has an alias of 'c'. So this has the same result as above::

    $ cmany c

You can skip the configure command and invoke build at once as if per
``cmake --build``. This will invoke ``cmany configure`` if necessary::

    $ cmany build

Same as above: 'b' is an alias to 'build'::

    $ cmany b

Same as above, and additionally install. That is, configure AND build AND install.
'i' is an alias to 'install'::

    $ cmany i

Choose a build type of Debug instead of Release::

    $ cmany b -t Debug

Build both Debug and Release build types (resulting in 2 build trees)::

    $ cmany b -t Debug,Release
    $ tree -fi -L 1 build/*
    build/linux-x86_64-gcc6.1-debug
    build/linux-x86_64-gcc6.1-release

Build using both clang++ and g++ (2 build trees)::

    $ cmany b -c clang++,g++
    $ tree -fi -L 1 build/*
    build/linux-x86_64-clang3.9-release
    build/linux-x86_64-gcc6.1-release

Build using both clang++,g++ and in Debug,Release modes (4 build trees)::

    $ cmany b -c clang++,g++ -t Debug,Release
    $ tree -fi -L 1 build/*
    build/linux-x86_64-clang3.9-debug
    build/linux-x86_64-clang3.9-release
    build/linux-x86_64-gcc6.1-debug
    build/linux-x86_64-gcc6.1-release

Build using clang++,g++,icpc in Debug,Release,RelWithDebInfo modes (9 build trees)::

    $ cmany b -c clang++,g++,icpc -t Debug,Release,MinSizeRel
    $ tree -fi -L 1 build/*
    build/linux-x86_64-clang3.9-debug
    build/linux-x86_64-clang3.9-relwithdebinfo
    build/linux-x86_64-clang3.9-release
    build/linux-x86_64-gcc6.1-debug
    build/linux-x86_64-gcc6.1-relwithdebinfo
    build/linux-x86_64-gcc6.1-release
    build/linux-x86_64-icc16.1-debug
    build/linux-x86_64-icc16.1-relwithdebinfo
    build/linux-x86_64-icc16.1-release

To get a list of available commands::

    $ cmany help

To get help on a particular command (eg, ``build``), either of the following can be used::

    $ cmany help build
    $ cmany build -h


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

License
-------

This project is licensed under the MIT license.

