Overview
========

Easily batch-build cmake projects!

`cmany <https://github.com/biojppm/cmany>`_ is a command line tool to easily
build variations of a CMake C/C++ project.  It combines different compilers,
cmake build types, compilation flags, processor architectures (WIP) and
operating systems (also WIP).

For example, to configure and build a project combining clang++ and g++
with both Debug and Release::

    $ cmany build -c clang++,g++ -t Debug,Release path/to/CMakeLists.txt

The command above will result in four different build trees, placed by default
under a ``build`` directory placed in the current working directory::

    $ ls build/*
    build/linux-x86_64-clang++3.9-Debug
    build/linux-x86_64-clang++3.9-Release
    build/linux-x86_64-gcc++6.1-Debug
    build/linux-x86_64-gcc++6.1-Release

Each build tree is obtained by first configuring CMake with the given
parameters, and then invoking ``cmake --build`` to build the project at once.

You can also use cmany just to simplify your cmake workflow! These two
command sequences have the same effect:

+-------------------------------+-------------------------------+
| typical cmake                 | cmany                         |
+===============================+===============================+
| | ``$ mkdir build``           | | ``$ cmany b``               |
| | ``$ cd build``              |                               |
| | ``$ cmake ..``              |                               |
| | ``$ cmake --build .``       |                               |
+-------------------------------+-------------------------------+

Features
--------
* Easily configures and builds many variations of your project with one
  simple command.
* Saves the tedious work of dealing with many build trees by hand.
* Sensible defaults: ``cmany build`` will create and build a single project
  using CMake's defaults.
* Transparently pass flags (compiler flags, processor defines or cmake cache
  variables) to any or all of the builds.
* Useful for build comparison and benchmarking. You can easily setup bundles
  of flags, aka variants.
* Useful for validating and unit-testing your project with different
  compilers and flags.
* Useful for creating distributions of your project.
* Avoids a full rebuild when the build type is changed. Although this feature
  already exists in multi-configuration cmake generators like Visual Studio,
  it is missing from mono-configuration generators like Unix Makefiles.
* Runs arbitrary commands in every build tree or install tree.
* Emacs integration! `<https://github.com/biojppm/cmany.el>`_

Contents
========

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   cmany
   installing
   quick_tour
   build_items
   excluding_builds
   flags
   vs
   dependencies
   reusing_arguments

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
