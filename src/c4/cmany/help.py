#!/usr/bin/env python3

import sys
from collections import OrderedDict as odict

topics = odict()


class Topic:

    keylen = 0
    tablefmt = None

    def __init__(self, id, title, doc, txt, disabled=False):
        self.id = id
        self.title = title
        self.doc = doc
        self.__doc__ = doc
        self.txt = txt
        Topic.keylen = max(Topic.keylen, len(id))
        Topic.tablefmt = '    {:' + str(Topic.keylen) + '} {}'
        if not disabled:
            topics[id] = self


def create_topic(id, title, doc, txt, disabled=False):
    ht = Topic(id, title, doc, txt, disabled)
    setattr(sys.modules[__name__], 'help_' + id, ht)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
create_topic(
    "examples",
    title="Basic usage examples",
    doc="Basic usage examples",
    txt="""Consider a directory with this layout::

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
""")


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
create_topic(
    "variants",
    title="Build variants",
    doc="help on specifying build variants",
    txt="""
    $ cmany b -v none,'noexcept: @none --cxxflags c++14,noexceptions --define V_NOEXCEPT','noexcept_static: @noexcept -DV_STATIC'

Making a variant inherit the properties of another variant
----------------------------------------------------------
""")


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
create_topic(
    "flags",
    title="Specifying flags",
    doc="help on command-line flag specification",
    txt="""
Specifying flags on the command line
------------------------------------

Using aliases
-------------

Built-in aliases
----------------

cmany provides built-in flag aliases to simplify working with different
compilers at the same time (eg, gcc and Visual Studio). The last

Defining more flag aliases
--------------------------

Save a flags aliases file named 'cmany_flags.yml'. Use the same format as


""")


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
create_topic(
    "vs",
    title="Visual Studio versions and toolsets",
    doc="help on specifying Microsoft Visual Studio versions and toolsets",
    txt="""
TODO: add help for visual studio

Visual Studio aliases example:
    vs2015_32: use 32bit version
    vs2015_64: use 64bit version
    vs2015:    use the bitness of the current system; will resolve into
               either vs2015_32 or vs2015_64
""")

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


epilog = """

list of help topics:
""" + '\n'.join([Topic.tablefmt.format(k, v.doc) for k, v in topics.items()])

