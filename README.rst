cmany
=====

Easily batch-build cmake projects!

cmany is a command line tool and Python3 module to easily build
several variations of a CMake C/C++ project. These variations
consist in combining different compilers, cmake build types, processor
architectures (WIP), operating systems (also WIP), or compilation flags (WIP).

For example, to configure and build a project using clang++ and g++
in both Debug and Release::

    $ cmany build -c clang++,g++ -b Debug,Release path/to/CMakeLists.txt

The command above will result in four different build trees, placed by default
under a ``build`` folder which is under the current folder::

    $ tree -fi -L1
    build
    build/linux-x86_64-clang3.9-Debug
    build/linux-x86_64-clang3.9-Release
    build/linux-x86_64-gcc6.1-Debug
    build/linux-x86_64-gcc6.1-Release

Features
--------

* Saves the tedious work of creating several build trees by hand.
* Useful for build comparisons.
* An added advantage is that a full rebuild is avoided when the build type
is changed. Although this feature is already present when using
multi-configuration cmake generators such as Visual Studio, this is
something that's been missing from mono-configuration generators like
Unix Makefiles.


Basic usage examples
--------------------

To get help::

    $ cmany help
    $ cmany build -h

Configure and build a CMakeLists.txt project located on the folder above
the current one. The build trees will be placed in separate folders under
a folder named "build" located on the current folder. Likewise, the installation
prefix will be set to a sister folder named "install". A c++ compiler will
be selected from the system, and the CMAKE_BUILD_TYPE will be set to Release::

    $ %(prog)s build ..

Same as above, but now look for CMakeLists.txt on the current dir::

    $ %(prog)s build .

Same as above: like with cmake, omitting the project dir defaults will cause
searching for CMakeLists.txt on the current dir::

    $ %(prog)s build

Same as above: 'b' is an alias to 'install'::

    $ %(prog)s b

Same as above, and additionally install. 'i' is an alias to 'install'::

    $ %(prog)s i

Only configure; do not build, do not install. 'c' is an alias to 'configure'::

    $ %(prog)s c

Build only the Debug build type::

    $ %(prog)s b -t Debug

Build both Debug and Release build types (resulting in 2 build trees)::

    $ %(prog)s b -t Debug,Release

Build using both clang++ and g++ (2 build trees)::

    $ %(prog)s b -c clang++,g++

Build using both clang++,g++ and in Debug,Release modes (4 build trees)::

    $ %(prog)s b -c clang++,g++ -t Debug,Release

Build using clang++,g++,icpc in Debug,Release,MinSizeRel modes (9 build trees)::

    $ %(prog)s b -c clang++,g++,icpc -t Debug,Release,MinSizeRel


Status
------

This project is under development, in pre-alpha.

Installation
------------

TODO.

Contribute
----------

TODO.

Support
-------

TODO.

License
-------

This project is licensed under the MIT license.

