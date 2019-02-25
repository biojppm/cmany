
|license|    |pypi|       |pyver|

|readthedocs|   |travis|     |appveyor|   |lgtm_grade|    |lgtm_alerts|


cmany
=====

Easily batch-build cmake projects!

`cmany <https://github.com/biojppm/cmany>`_ is a command line tool to easily
build variations of a CMake C/C++ project.  It combines different compilers,
cmake build types, bundles of compilation flags, processor architectures and
operating systems. Each of these items can also have associated compilation
flags.

For example, to configure and build a project combining clang++ and g++
with both Debug and Release::

    $ cmany build -c clang++,g++ -t Debug,Release path/to/CMakeLists.txt

The command above will result in four different build trees, placed by default
under a ``build`` subdirectory in the current working directory::

    $ ls build/*
    build/linux-x86_64-clang++3.9-Debug
    build/linux-x86_64-clang++3.9-Release
    build/linux-x86_64-gcc++6.1-Debug
    build/linux-x86_64-gcc++6.1-Release

Each build tree is obtained by first configuring the project with the items
in each combination, and then invoking ``cmake --build`` to build the project
at once.

You can also use cmany just to simplify your cmake workflow! These two
command sequences have the same effect (``b`` is an alias to ``build``):

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
* Saves the tedious and error-prone work of dealing with many build trees by
  hand.
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
* Full control over how the build items are combined.
* Emacs integration! `<https://github.com/biojppm/cmany.el>`_

More info
---------
* `Project home <https://github.com/biojppm/cmany>`_
* `Installing <https://cmany.readthedocs.io/en/latest/installing/>`_
* `Getting started <https://cmany.readthedocs.io/en/latest/quick_tour/>`_

Support
-------
* send bug reports to `<https://github.com/biojppm/cmany/issues>`_.
* send pull requests to `<https://github.com/biojppm/cmany/pulls>`_.

Current status
--------------
cmany is in beta state, under current development.

Limitations & Known issues
^^^^^^^^^^^^^^^^^^^^^^^^^^

* cmany invokes the compilers given to it to find their name and version. So
  far, this successfully works with Visual Studio, gcc (also with arm-linux and
  mips-linux counterparts), clang, icc and zapcc. However, the current
  implementation for guessing the name and version is fragile and may fail in
  some compilers which were not tested. Please submit a bug or PR if you
  see such a failure.
* Though cmany works in OS X with gcc and clang, using Xcode has not been
  tested at all. Get in touch if you are interested in getting cmany to work
  with Xcode.
* Pure C projects (ie not C++) should work but have not yet been tested. Some
  bugs may be present.

License
-------
cmany is permissively licensed under the `MIT license`_.


.. _MIT license: LICENSE.txt

.. |license| image:: https://img.shields.io/badge/License-MIT-green.svg?style=plastic
   :alt: License: MIT
   :target: https://github.com/biojppm/cmany/blob/master/LICENSE.txt

.. |pypi| image:: https://img.shields.io/pypi/v/cmany.svg?color=green&style=plastic
   :alt: Version
   :target: https://pypi.org/project/cmany/

.. |pyver| image:: https://img.shields.io/badge/python-3.4+-green.svg?style=plastic
    :alt: Supported Python versions
    :target: https://www.python.org/download/releases/3.4.0/

.. |travis| image:: https://img.shields.io/travis/biojppm/cmany.svg?style=plastic
    :alt: Linux+OSX build status
    :target: https://travis-ci.org/biojppm/cmany

.. |appveyor| image:: https://img.shields.io/appveyor/ci/biojppm/cmany.svg?style=plastic
    :alt: Windows build status
    :target: https://ci.appveyor.com/project/biojppm/cmany

.. |readthedocs| image:: https://img.shields.io/readthedocs/cmany.svg?style=plastic
    :alt: Documentation status
    :target: https://cmany.readthedocs.io/

.. |lgtm_grade| image:: https://img.shields.io/lgtm/grade/python/g/biojppm/cmany.svg?style=plastic
    :alt: LGTM Grade
    :target: https://lgtm.com/projects/g/biojppm/cmany/

.. |lgtm_alerts| image:: https://img.shields.io/lgtm/alerts/g/biojppm/cmany.svg?style=plastic
    :alt: LGTM Alerts
    :target: https://lgtm.com/projects/g/biojppm/cmany/alerts/?mode=list
