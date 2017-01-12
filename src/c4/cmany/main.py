#!/usr/bin/env python3

import sys
import pprint
import argparse
import re
from collections import OrderedDict as odict

from c4.cmany import cmany
from c4.cmany import util
from c4.cmany.util import cslist
from c4.cmany.cmany import cpu_count


cmds = odict([
    ('help', ['h']),
    ('configure', ['c']),
    ('build', ['b']),
    ('install', ['i']),
#    ('create', []),
    ('showvars', []),
])


def cmany_main(in_args=None):
    '''Easily process several build trees of a CMake project'''
    if in_args is None: in_args = sys.argv[1:]
    p = argparse.ArgumentParser(prog='cmany',
                                description=__doc__,
                                usage='%(prog)s [-h] subcommand [-h]',
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog=_help_epilog)
    sp = p.add_subparsers(help='')
    p.add_argument('--show-args', action='store_true', help=argparse.SUPPRESS)
    p.add_argument('--dump-help-topics', action='store_true', help=argparse.SUPPRESS)
    for cmd, aliases in cmds.items():
        cl = getattr(sys.modules[__name__], cmd)
        h = sp.add_parser(name=cmd, aliases=aliases, help=cl.__doc__)
        cl().add_args(h)
        def exec_cmd(args, cmd_class=cl):
            obj = cmd_class()
            proj = obj.proj(args)
            obj._exec(proj, args)
        h.set_defaults(func=exec_cmd)
    args = p.parse_args(in_args)
    if args.show_args:
        pprint.pprint(vars(args), indent=4)
    if args.dump_help_topics:
        dump_help_topics()
    if not hasattr(args, 'func'):
        argerror('missing subcommand')
    args.func(args)


def argerror(*msg_args):
    print(*msg_args, end='')
    print('\n')
    cmany_main(['-h'])
    exit(1)


class FlagArgument(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        def isquoted(s):
            return (s[0] == "'" and s[-1] == "'") or (s[0] == '"' and s[-1] == '"')
        li = getattr(namespace, self.dest)
        v = values
        if isquoted(v):
            if not (re.search(r'","', v) or re.search(r"','", v)):
                v = v[1:-1]
        livals = cslist(v)
        for l in livals:
            if isquoted(l):
                l = l[1:-1]
            li.append(l)
        setattr(namespace, self.dest, li)


# -----------------------------------------------------------------------------
def add_flag_opts(parser):
    g = parser.add_argument_group('CMake variables, build flags and defines')
    g.add_argument("-V", "--vars", metavar="var1=val1,var2=val2,...",
                   default=[], action=FlagArgument,
                   help="""Add cmake variables to all builds.
                   Multiple invokations of -K are possible, in which case
                   arguments will be appended and not overwritten.
                   Can also be given as a comma-separated list.
                   To escape commas, use a backslash \\.""")
    g.add_argument("-D", "--defines", default=[], action=FlagArgument,
                   help="""add a preprocessor symbol definition to all builds.
                   Multiple invokations of -D are possible, in which case
                   arguments will be appended and not overwritten.
                   Can also be given as a comma-separated list.
                   To escape commas, use a backslash \\.""")
    g.add_argument("-X", "--cxxflags", default=[], action=FlagArgument,
                   help="""add C++ compiler flags applying to all builds.
                   These will be passed to cmake by appending to the
                   default initial value of CMAKE_CXX_FLAGS (taken from
                   CMAKE_CXX_FLAGS_INIT). cmany has flag aliases mapping
                   to several common compilers. Type `cmany help flags`
                   to get help about this.
                   Multiple invokations of -X are possible, in which case
                   arguments will be appended and not overwritten.
                   Can also be given as a comma-separated list.
                   To escape commas, use a backslash \\.""")
    g.add_argument("-C", "--cflags", default=[], action=FlagArgument,
                   help="""add C compiler flags applying to all builds.
                   These will be passed to cmake by appending to the
                   default initial value of CMAKE_C_FLAGS (taken from
                   CMAKE_C_FLAGS_INIT). cmany has flag aliases mapping
                   to several common compilers. Type `cmany help flags`
                   to get help about this.
                   Multiple invokations of -X are possible, in which case
                   arguments will be appended and not overwritten.
                   Can also be given as a comma-separated list.
                   To escape commas, use a backslash \\.""")
    # g.add_argument("-I", "--include-dirs", default=[], action=FlagArgument,
    #                help="""add dirs to the include path of all builds
    #                Multiple invokations of -I are possible, in which case arguments will be appended and not overwritten.
    #                Can also be given as a comma-separated list. To escape commas, use a backslash \\.""")
    # g.add_argument("-L", "--link-dirs", default=[], action=FlagArgument,
    #                help="""add dirs to the link path of all builds
    #                Multiple invokations of -L are possible, in which case arguments will be appended and not overwritten.
    #                Can also be given as a comma-separated list. To escape commas, use a backslash \\.""")


class cmdbase:
    '''base class for commands'''
    def add_args(self, parser):
        '''add arguments to a command parser'''
        pass
    def proj(self, args):
        '''create a project given the configuration.'''
        return cmany.ProjectConfig(**vars(args))
    def _exec(self, proj, args):
        assert False, 'never call the base class method. Implement this in derived classes'


class projcmd(cmdbase):
    '''a command which refers to a project'''
    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument("proj-dir", nargs="?", default=".",
                            help="""the directory where the project's CMakeLists.txt is located. An empty argument
                            will default to the current directory ie, \".\". Passing a directory
                            which does not contain a CMakeLists.txt will cause an error.""")
        parser.add_argument("--build-dir", default="./build",
                            help="set the build root (defaults to ./build)")
        parser.add_argument("--install-dir", default="./install",
                            help="set the install root (defaults to ./install)")
        parser.add_argument("-j", "--jobs", default=cpu_count(),
                            help="""build with the given number of parallel jobs
                            (defaults to %(default)s on this machine).""")
        add_flag_opts(parser)


class selectcmd(projcmd):
    '''a command which selects several builds'''
    def add_args(self, parser):
        super().add_args(parser)
        g = parser.add_argument_group(title="Selecting the builds")
        g.add_argument("-s", "--systems", metavar="os1,os2,...",
                       default=[cmany.System.default_str()], type=cslist,
                       help="""(WIP) restrict actions to the given operating systems.
                       Defaults to the current system, \"%(default)s\".
                       Provide as a comma-separated list. To escape commas, use a backslash \\.
                       This feature is a stub only and is still to be implemented.""")
        g.add_argument("-a", "--architectures", metavar="arch1,arch2,...",
                       default=[cmany.Architecture.default_str()], type=cslist,
                       help="""(WIP) restrict actions to the given processor architectures.
                       Defaults to CMake's default architecture, \"%(default)s\" on this system.
                       Provide as a comma-separated list. To escape commas, use a backslash \\.
                       This feature requires os-specific toolchains and is currently a
                       work-in-progress.""")
        g.add_argument("-c", "--compilers", metavar="compiler1,compiler2,...",
                       default=[cmany.Compiler.default_str()], type=cslist,
                       help="""restrict actions to the given compilers.
                       Provide as a comma-separated list. To escape commas, use a backslash \\.
                       Defaults to CMake's default compiler, \"%(default)s\" on this system.""")
        g.add_argument("-t", "--build-types", metavar="type1,type2,...",
                       default=["Release"], type=cslist,
                       help="""restrict actions to the given build types.
                       Provide as a comma-separated list. To escape commas, use a backslash \\.
                       Defaults to \"%(default)s\".""")
        g.add_argument("-v", "--variants", metavar="variant1,variant2,...",
                       default=[], type=cslist,
                       help="""(WIP) restrict actions to the given variants.
                       Provide as a comma-separated list. To escape commas, use a backslash \\.
                       This feature is currently a work-in-progress.""")


class help(cmdbase):
    '''get help on a particular subcommand or topic. Available topics:
    basic_examples, flags, visual_studio.'''
    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument('subcommand_or_topic', default="", nargs='?')

    def _exec(self, proj, args):
        sct = args.subcommand_or_topic
        if not sct:
            cmany_main(['-h'])
        else:
            sc = cmds.get(sct)
            # is it a subcommand?
            if sc is not None:
                cmany_main([sct, '-h'])
            else:
                # is it a topic?
                subtopic = help_topics.get(args.subcommand_or_topic)
                if subtopic is None:
                    msg = ("{} is not a subcommand or topic.\n" +
                           "Available subcommands are: {}\n" +
                           "Available help topics are: {}\n")
                    print(msg.format(args.subcommand_or_topic,
                                     ', '.join(cmds.keys()),
                                     ', '.join(help_topics.keys())))
                    exit(1)
                else:
                    print(subtopic.txt)


class configure(selectcmd):
    '''configure the selected builds'''
    def _exec(self, proj, args):
        proj.configure()


class build(selectcmd):
    '''build the selected builds, configuring before if necessary'''
    def _exec(self, proj, args):
        proj.build()


class install(selectcmd):
    '''install the selected builds, building before if necessary'''
    def _exec(self, proj, args):
        proj.install()


"""
class create(selectcmd):
    '''create a CMakeSettings.json file with the given combination of build parameters'''
    def _exec(self, proj, args):
        print("creating", os.path.join(proj.rootdir, "CMakeSettings.json"))
"""


class showvars(selectcmd):
    '''show the value of certain CMake cache vars'''
    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument('var_names', default="", nargs='+')

    def _exec(self, proj, args):
        proj.showvars(args.var_names)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


help_topics = odict()


class HelpTopic:

    keylen = 0
    tablefmt = None

    def __init__(self, id, title, doc, txt, disabled=False):
        self.id = id
        self.title = title
        self.doc = doc
        self.__doc__ = doc
        self.txt = txt
        HelpTopic.keylen = max(HelpTopic.keylen, len(id))
        HelpTopic.tablefmt = '    {:' + str(HelpTopic.keylen) + '} {}'
        if not disabled:
            help_topics[id] = self


def create_help_topic(id, title, doc, txt, disabled=False):
    ht = HelpTopic(id, title, doc, txt, disabled)
    setattr(sys.modules[__name__], 'help_' + id, ht)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
create_help_topic(
    "basic_examples",
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
    build/linux-x86_64-clang3.9-relwithdebinfo/
    build/linux-x86_64-clang3.9-release/
    build/linux-x86_64-gcc6.1-debug/
    build/linux-x86_64-gcc6.1-relwithdebinfo/
    build/linux-x86_64-gcc6.1-release/
    build/linux-x86_64-icc16.1-debug/
    build/linux-x86_64-icc16.1-relwithdebinfo/
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
create_help_topic(
    "dir_formats",
    disabled=True,
    title="Specifying directory patterns",
    doc="help on dir formats",
    txt="""
    $ cmany -I "path/to/{system}-{architecture}-{compiler}-{build_type}{variant?-{variant}}"
""")


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
create_help_topic(
    "flags",
    title="Preset compiler flags",
    doc="help on dir formats",
    txt="""
TODO: add help for compiler flags
""")


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
create_help_topic(
    "variants",
    title="Build variants",
    doc="help on specifying variants",
    txt="""
    $ cmany b -v none,'noexcept: @none --cxxflags c++14,noexceptions --define V_NOEXCEPT','noexcept_static: @noexcept -DV_STATIC'
""")


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
create_help_topic(
    "visual_studio",
    title="Visual Studio versions and toolsets",
    doc="help on specifying Microsoft Visual Studio versions and toolsets",
    txt="""
TODO: add help for visual studio

Visual Studio aliases example:
    vs2013: use the bitness of the current system
    vs2013_32: use 32bit version
    vs2013_64: use 64bit version
""")

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


_help_epilog = """

list of help topics:
""" + '\n'.join([HelpTopic.tablefmt.format(k, v.doc) for k, v in help_topics.items()])


def dump_help_topics():
    for t, _ in help_topics.items():
        print(t)
        txt = util.runsyscmd([sys.executable, sys.modules[__name__].__file__,
                              'help', t], echo_cmd=False, capture_output=True)
        print(txt)

# -----------------------------------------------------------------------------

if __name__ == "__main__":

    cmany_main(sys.argv[1:])
