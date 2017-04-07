Installing
==========

Requirements
------------
* CMake
* Python 3.3+
* pip

Installing from PyPI
--------------------
cmany will eventually be added to the PyPI repository so that you can install
via pip, but for now you can install it from source; see below.

Installing from source
----------------------
Installing from source is easy with pip::

  $ git clone https://github.com/biojppm/cmany
  $ cd cmany
  $ pip install .

If you want to develop cmany, use the ``-e`` option for pip so that any
changes you make to cmany's sources are always reflected to the installed
version::

  $ pip install -e .

Uninstalling
------------
To uninstall cmany, just use pip::

  $ pip uninstall cmany
