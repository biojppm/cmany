#!/usr/bin/env python3

import sys
import re
import argparse

from . import util, cmany, help
from .util import cslist
from .cmany import cpu_count


# -----------------------------------------------------------------------------
def setup(subcommands, module):
    p = argparse.ArgumentParser(prog='cmany',
                                description='''Easily process several build trees of a CMake project''',
                                usage='%(prog)s',
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog=help.epilog)
    sp = p.add_subparsers(help='')
    add_hidden(p)
    for cmd, aliases in subcommands.items():
        cl = getattr(module, cmd)
        h = sp.add_parser(name=cmd, aliases=aliases, help=cl.__doc__)
        cl().add_args(h)
        def exec_cmd(args, cmd_class=cl):
            obj = cmd_class()
            proj = obj.proj(args)
            obj._exec(proj, args)
        h.set_defaults(func=exec_cmd)
    return p


def parse(parser, in_args):
    args = parser.parse_args(in_args)
    if not hasattr(args, 'func'):
        argerror(parser, 'missing subcommand')
    return args


def argerror(parser, *msg_args):
    print(*msg_args, end='')
    print('\n')
    parse(parser, ['-h'])
    exit(1)


# -----------------------------------------------------------------------------
def add_hidden(parser):
    parser.add_argument('--show-args', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--dump-help-topics', action='store_true', help=argparse.SUPPRESS)


# -----------------------------------------------------------------------------
def add_proj(parser):
    parser.add_argument("proj_dir", nargs="?", default=".",
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


# -----------------------------------------------------------------------------
def add_select(parser):
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
                   default=[], action=VariantArgument,
                   help="""(WIP) restrict actions to the given variants.
                   Provide as a comma-separated list. To escape commas, use a backslash \\.
                   This feature is currently a work-in-progress.""")


# -----------------------------------------------------------------------------
def add_cflags(parser):
    g = parser.add_argument_group('CMake variables, build flags and defines')
    g.add_argument("-V", "--vars", metavar="var1=val1,var2=val2,...",
                   default=[], action=FlagArgument,
                   help="""Add CMake cache variables to all builds.
                   Multiple invokations of are possible, in which case
                   arguments will be appended and not overwritten.
                   Can also be given as a comma-separated list, including in
                   each invokation.
                   To escape commas, use a backslash \\.""")
    g.add_argument("-D", "--defines", default=[], action=FlagArgument,
                   help="""add a preprocessor symbol definition to all builds.
                   Multiple invokations of -D are possible, in which case
                   arguments will be appended and not overwritten.
                   Can also be given as a comma-separated list, including in
                   each invokation.
                   To escape commas, use a backslash \\.""")
    g.add_argument("-X", "--cxxflags", default=[], action=FlagArgument,
                   help="""add C++ compiler flags applying to all builds.
                   These will be passed to cmake by appending to the
                   default initial value of CMAKE_CXX_FLAGS (taken from
                   CMAKE_CXX_FLAGS_INIT). cmany has flag aliases mapping
                   to several common compilers. Run `cmany help flags`
                   to get help about this.
                   Multiple invokations of -X are possible, in which case
                   arguments will be appended and not overwritten.
                   Can also be given as a comma-separated list, including in
                   each invokation.
                   To escape commas, use a backslash \\.""")
    g.add_argument("-C", "--cflags", default=[], action=FlagArgument,
                   help="""add C compiler flags applying to all builds.
                   These will be passed to cmake by appending to the
                   default initial value of CMAKE_C_FLAGS (taken from
                   CMAKE_C_FLAGS_INIT). cmany has flag aliases mapping
                   to several common compilers. Run `cmany help flags`
                   to get help about this.
                   Multiple invokations of -X are possible, in which case
                   arguments will be appended and not overwritten.
                   Can also be given as a comma-separated list, including in
                   each invokation.
                   To escape commas, use a backslash \\.""")
    g.add_argument("--flags-file", default=['cmany_flags.yml'], action="append",
                   help="""Specify a file containing flag aliases. Relative
                   paths are assumed from the top level CMakeLists.txt file.
                   Run `cmany help flags` to get help about flag aliases.
                   Multiple invokations are possible, in which case flags
                   given in latter files will prevail over those of earlier
                   files.""")
    g.add_argument("--no-default-flags", default=False, action="store_true",
                   help="""Do not read the default cmany flag alias file. Run
                   `cmany help flags` to get help about this.""")
    # g.add_argument("-I", "--include-dirs", default=[], action=FlagArgument,
    #                help="""add dirs to the include path of all builds
    #                Multiple invokations of -I are possible, in which case arguments will be appended and not overwritten.
    #                Can also be given as a comma-separated list. To escape commas, use a backslash \\.""")
    # g.add_argument("-L", "--link-dirs", default=[], action=FlagArgument,
    #                help="""add dirs to the link path of all builds
    #                Multiple invokations of -L are possible, in which case arguments will be appended and not overwritten.
    #                Can also be given as a comma-separated list. To escape commas, use a backslash \\.""")


# -----------------------------------------------------------------------------
class FlagArgument(argparse.Action):
    """a class to be used by argparse when parsing arguments which are compiler flags"""
    def __call__(self, parser, namespace, values, option_string=None):
        li = getattr(namespace, self.dest)
        v = values
        # remove start and end quotes if there are any
        if util.is_quoted(v):
            v = util.unquote(v)
        # split at commas
        livals = cslist(v)
        # unquote splits
        for l in livals:
            ul = util.unquote(l)
            li.append(ul)
        setattr(namespace, self.dest, li)


# -----------------------------------------------------------------------------
class VariantArgument(argparse.Action):
    """a class to be used by argparse when parsing variant specifications.
    Note that prettyprint shows variants wrong.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        li = getattr(namespace, self.dest)
        util.logwarn("input: ", li, " + ===" + values + "===")
        vli = cmany.Variant.parse_specs(values)
        li += vli
        util.logerr("result:", li)
        setattr(namespace, self.dest, li)
