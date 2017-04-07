
===========  ===============  ========================  ======================
 |license|    |readthedocs|    Linux + OS X: |travis|    Windows: |appveyor|
===========  ===============  ========================  ======================

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
under a ``build`` directory placed in the current working directory::

    $ ls build/*
    build/linux-x86_64-clang3.9-Debug
    build/linux-x86_64-clang3.9-Release
    build/linux-x86_64-gcc6.1-Debug
    build/linux-x86_64-gcc6.1-Release

Each build tree is obtained by first configuring CMake with the given
parameters, and then invoking ``cmake --build`` to build the project at once.

You can also use cmany just to simplify your daily cmake
workflow! These two command sequences have the same effect:

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

Requirements
^^^^^^^^^^^^
* CMake
* Python 3.3+
* pip

PyPI
^^^^
cmany will eventually be added to the PyPI repository so that you can install
via pip, but for now you can install it from source; see below.

From source
^^^^^^^^^^^
::
  $ git clone https://github.com/biojppm/cmany
  $ cd cmany
  $ pip install .

If you want to develop cmany, use the ``-e`` option for pip so that any
changes you make are always reflected to the installed version::

  $ pip install -e .

Getting started
---------------
Read `the quick tour <https://cmany.readthedocs.io/>`_ in cmany's documentation.

Status
------
This project is a pre-alpha under development.

Contribute
----------
Send pull requests to `<https://github.com/biojppm/cmany/pulls>`_.

Support
-------
Send bug reports to `<https://github.com/biojppm/cmany/issues>`_.

Known issues
------------
* cmany will invoke the compilers given to it to find their name and
  version. So far, this successfully works with Visual Studio, gcc, clang,
  icc and zapcc. However, the current implementation of this logic is fragile
  and may fail in some cases. Please submit a bug or PR if you experience
  such a failure.
* Pure C projects (ie not C++) should work but have not yet been extensively
  tested. Some bugs may be present.

License
-------
This project is permissively licensed under the `MIT license`_.

.. _MIT license: LICENSE.txt

.. |license| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :alt: License: MIT
   :target: https://opensource.org/licenses/MIT
.. |travis| image:: https://travis-ci.org/biojppm/cmany.svg?branch=master
    :alt: Linux+OSX build status
    :target: https://travis-ci.org/biojppm/cmany
.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/biojppm/cmany?branch=master&svg=true
    :alt: Windows build status
    :target: https://ci.appveyor.com/project/biojppm/cmany
.. |readthedocs| image:: https://readthedocs.org/projects/docs/badge/?version=latest
    :alt: Documentation status
    :target: https://cmany.readthedocs.io/
