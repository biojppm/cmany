cmany
=====

Easily batch-build cmake projects!

cmany is a command line tool to easily build variations of a CMake C/C++ project.
It combines different compilers, cmake build types, compilation flags,
processor architectures (WIP) and operating systems (also WIP).

For example, to configure and build a project combining clang++ and g++
with both Debug and Release::

    $ cmany build -c clang++,g++ -t Debug,Release path/to/CMakeLists.txt

The command above will result in four different build trees, placed by default
under a ``build`` directory which is under the current working directory::

    $ ls build/*
    build/linux-x86_64-clang3.9-Debug
    build/linux-x86_64-clang3.9-Release
    build/linux-x86_64-gcc6.1-Debug
    build/linux-x86_64-gcc6.1-Release

Each build tree is obtained by first configuring CMake with the given
parameters, and then invoking ``cmake --build`` to build the project at once.

You can also just use cmany as a much simpler version of the typical
cmake usage pattern:

+-------------------------------+-------------------------------+
| typical cmake                 | cmany                         |
+===============================+===============================+
| | ``$ git clone <some-repo>`` | | ``$ git clone <some-repo>`` |
| | ``$ cd <some-repo>``        | | ``$ cd <some-repo>``        |
| | ``$ mkdir build``           | | ``$ cmany b``               |
| | ``$ cd build``              |                               |
| | ``$ cmake ..``              |                               |
| | ``$ cmake --build .``       |                               |
+-------------------------------+-------------------------------+

Features
--------
* Easily configure and build many variations of your project with one simple command.
* Saves the tedious work of dealing with many build trees by hand.
* Sensible defaults: ``cmany build`` will create and build a single project using CMake's
  defaults.
* Transparently pass flags (compiler flags, processor defines  or cmake cache
  variables) to any or all of the builds.
* Useful for build comparisons. You can easily setup bundles of flags, aka variants.
* Useful for validating and unit-testing your project with different
  compilers and flags.
* Useful for creating distributions.
* Avoids a full rebuild when the build type is changed. Although this feature
  already exists in multi-configuration cmake generators like Visual
  Studio, it is missing from mono-configuration generators like Unix
  Makefiles.
* Run arbitrary commands in every build tree or install tree.
* Emacs integration! `<https://github.com/biojppm/cmany.el>`_


Installing
----------
cmany is written in Python 3. It will eventually be added to the PyPI repository, but for
now you can install it from a repo clone::

  $ git clone https://github.com/biojppm/cmany
  $ cd cmany
  $ pip3 install .

If you want to install and develop cmany, use the ``-e`` option for pip::

  $ pip3 install -e .


Getting started
---------------
Read `the quick tour <https://cmany.readthedocs.io/>`_ in cmany's documentation.

License
-------
This project is licensed under the MIT license.

Status
------
This project is a pre-alpha under development.

Contribute
----------
Send pull requests to `<https://github.com/biojppm/cmany/pulls>`_.

Support
-------
Send bug reports to `<https://github.com/biojppm/cmany/issues>`_.


Contents
========

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   index
   quick_tour
   flags
   variants
   vs

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
