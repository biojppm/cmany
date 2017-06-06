#!/usr/bin/env python3

import argparse
import pprint
import os

from . import util
from . import help
from . import system
from . import build_item
from . import architecture
from . import compiler

from .util import cslist
from multiprocessing import cpu_count as cpu_count


# -----------------------------------------------------------------------------
def setup(subcommands, module):
    """creates a parser to process cmany's arguments"""
    p = argparse.ArgumentParser(
        prog='cmany',
        description='''Easily process several build trees of a CMake project''',
        usage='%(prog)s',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=help.epilog
    )
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
    """parses and performs related tasks"""
    args = parser.parse_args(in_args)
    if not hasattr(args, 'func'):
        argerror(parser, 'missing subcommand')
    if _handle_hidden_args__skip_rest(args):
        return None
    return args


def argerror(parser, *msg_args):
    print(*msg_args, end='')
    print('\n')
    parse(parser, ['-h'])
    exit(1)


def merge_envargs(cmds, sysargs):
    """gets any arguments from environment vars"""
    #
    pfxargs = os.environ.get('CMANY_PFX_ARGS', '')
    pfxargs = util.splitesc_quoted(pfxargs, ' ')
    pfxargs = [util.unquote(a) for a in pfxargs]
    #
    cmdargs = os.environ.get('CMANY_ARGS', '')
    cmdargs = util.splitesc_quoted(cmdargs, ' ')
    cmdargs = [util.unquote(a) for a in cmdargs]
    #
    if not pfxargs and not cmdargs:
        return sysargs
    #
    pos = find_subcommand(cmds, sysargs)
    args = sysargs
    cmd = sysargs[pos]
    if cmd not in ('help', 'h'):
        args = sysargs[0:pos]
        if pfxargs:
            # print("inserting CMANY_PFX_ARGS:", pfxargs)
            args += pfxargs
        args.append(cmd)
        if cmdargs:
            # print("inserting CMANY_ARGS:", cmdargs)
            args += cmdargs
        if len(sysargs) > pos+1:
            args += sysargs[(pos+1):]
    # print("resulting args:", args)
    return args


def find_subcommand(cmds, args):
    pos = None
    for i, a in enumerate(args):
        for c, aliases in cmds.items():
            if a == c or a in aliases:
                pos = i
                return pos
    raise Exception("could not find subcommand")


# -----------------------------------------------------------------------------
def add_hidden(parser):
    parser.add_argument('--show-args', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--only-show-args', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--show-args-list', type=cslist, default=[], help=argparse.SUPPRESS)
    parser.add_argument('--only-show-args-list', type=cslist, default=[], help=argparse.SUPPRESS)


def _handle_hidden_args__skip_rest(args):
    if args.show_args or args.only_show_args:
        pprint.pprint(vars(args), indent=4)
        if args.only_show_args:
            return True
    if args.show_args_list or args.only_show_args_list:
        l = args.show_args_list + args.only_show_args_list
        for a in l:
            print("args[", a, "]: ", sep='', end='')
            if not hasattr(args, a):
                print("(does not exist!)")
                continue
            v = getattr(args, a)
            pprint.pprint(v, indent=4)
        if args.only_show_args_list:
            return True
    return False


# -----------------------------------------------------------------------------
def add_proj(parser):
    parser.add_argument("proj_dir", nargs="?", default=".",
                        help="""the directory where the project's CMakeLists.txt
                        is located. An empty argument will default to the
                        current directory ie, \".\". Passing a directory which
                        does not contain a CMakeLists.txt will cause an error.""")
    parser.add_argument("--build-dir", default="./build",
                        help="set the build root (defaults to ./build)")
    parser.add_argument("--install-dir", default="./install",
                        help="set the install root (defaults to ./install)")
    parser.add_argument("-j", "--jobs", default=cpu_count(),
                        help="""build with the given number of parallel jobs
                        (defaults to %(default)s on this machine).""")
    parser.add_argument("-E", "--export-compile", default=False,
                        action="store_true",
                        help="""Have cmake export a compile_commands.json
                        containing the compile commands for each file. This
                        is useful eg for clang-based indexing tools.""")

    g = parser.add_argument_group('Configuration files')
    g.add_argument("--config-file", default=[], action="append",
                   help="""Specify a file containing configurations. Relative
                   paths are taken from the project's CMakeLists.txt directory.
                   Run `cmany help flags` to get help about flag aliases.
                   Multiple invokations are possible, in which case flags
                   given in latter files will prevail over those of earlier
                   files.""")
    g.add_argument("--no-default-config", default=False, action="store_true",
                   help="""Do not read the default config file. Run
                   `cmany help flags` to get help about this.""")

    d = parser.add_argument_group('Dependencies')
    d.add_argument('--deps', default='', type=str,
                   metavar='path/to/extern/CMakeLists.txt',
                   help="""Before configuring, process (ie, configure, build
                   and install) the given CMakeLists.txt project containing
                   needed external project dependencies. This will be done
                   separately for each build, using the same parameters. The
                   main project will be configured such that the built
                   dependencies are found by cmake.""")
    d.add_argument('--deps-prefix', default="", type=str,
                   metavar='path/to/install/directory',
                   help="""When using --deps set the install directory for
                   external dependencies to the given dir.""")
    d.add_argument('--with-conan', action='store_true', default=False,
                   help="""(WIP)""")


# -----------------------------------------------------------------------------
def _item_printer(dft):
    s = "["
    for i, item in enumerate(dft):
        if i > 1: s += ","
        s += str(item).replace(' ', '\ ')
    s += "]"
    return s


def add_select(parser):
    g = parser.add_argument_group(
        title="Build items",
        description="""Items to be combined by cmany. Each item can be made to
        bring specific flags with it by using the syntax 'item_name:
        <flags>...' (the quotes are needed when this syntax is used). Run
        `cmany help flags` to see the possible flags. Items can be
        given either as a comma-separated list or with repeated invokations
        of their arguments. Commas can be escaped by using a backslash,
        \\.""")

    dft = [system.System.default_str()]
    g.add_argument("-s", "--systems", metavar="os1,os2,...",
                   default=dft, action=BuildItemArgument,
                   help="""Specify a comma-separated list of operating systems
                   to combine. Defaults to the current system, """ +
                   _item_printer(dft) + """.""")

    dft = [architecture.Architecture.default_str()]
    g.add_argument("-a", "--architectures", metavar="arch1,arch2,...",
                   default=dft, action=BuildItemArgument,
                   help="""Specify a comma-separated list of processor
                   architectures to combine. Defaults to CMake's default
                   architecture on this system, """ +
                   _item_printer(dft) + """.""")

    dft = [compiler.Compiler.default_str()]
    g.add_argument("-c", "--compilers", metavar="compiler1,compiler2,...",
                   default=dft, action=BuildItemArgument,
                   help="""Specify a comma-separated list of compilers to
                   combine. Compilers can be given as an absolute path, or as
                   a name, in which case that name will be searched for in
                   the current shell's PATH.  Defaults to CMake's default
                   compiler on this system, """ +
                   _item_printer(dft) + """.""")

    # dft = [build_type.BuildType.default_str()]  # avoid a circular dependency
    dft = ["Release"]
    g.add_argument("-t", "--build-types", metavar="type1,type2,...",
                   default=dft, action=BuildItemArgument,
                   help="""Specify a comma-separated list of build types
                   to combine. Defaults to """ + _item_printer(dft) + """.""")

    # dft = [variant.Variant.default_str()]  # avoid a circular dependency
    dft = ["none"]
    g.add_argument("-v", "--variants", metavar="variant1,variant2,...",
                   default=["none"], action=BuildItemArgument,
                   help="""Specify a comma-separated list of variants
                   to combine. The variant name 'none' is special and will be
                   omitted from the name of the resulting build. Defaults to
                   """ + _item_printer(dft) + """.""")
    #add_combination_flags(parser)


# -----------------------------------------------------------------------------
def add_bundle_flags(parser):
    add_cflags(parser)
    add_combination_flags(parser)
    add_item_combination_flags(parser)


def add_combination_flags(parser):
    g = parser.add_argument_group(
        'Combination rules',
        description="""Prevent certain build item combinations from producing
                    a build. The rules in each argument are Python regular
                    expressions that are matched against each build name.
                    A build is included only if its name successfully matches
                    every combination argument. The build name is of the form
                    {system}-{architecture}-{compiler}-{build_type}[-{variant}].
                    The arguments are matched in the given order.""")
    g.add_argument("-xb", "--exclude-builds", metavar="rule1,[rule2[,...]]",
                   default=[], action=CombinationArgument,
                   help="""Exclude build item combinations whose name
                   matches ANY rule in the list.""")
    g.add_argument("-ib", "--include-builds", metavar="rule1,[rule2[,...]]",
                   default=[], action=CombinationArgument,
                   help="""Only allow build item combinations whose name
                   matches ANY rules in the list.""")
    g.add_argument("-xba", "--exclude-builds-all", metavar="rule1,[rule2[,...]]",
                   default=[], action=CombinationArgument,
                   help="""Exclude build item combinations whose name
                   matches ALL rules in the list.""")
    g.add_argument("-iba", "--include-builds-all", metavar="rule1,[rule2[,...]]",
                   default=[], action=CombinationArgument,
                   help="""Only allow build item combinations whose name
                   matches ALL rules in the list.""")


def add_item_combination_flags(parser):
    g = parser.add_argument_group(
        'Build-item-specific combination rules',
        description="""Prevent certain build items from producing a build.
        Each item is given by name and must be valid. These arguments are
        generally for use in specifications of build items; however, they may
        also be of use when using arguments via the CMANY_ARGS environment
        or with a project file.""")

    g.add_argument("-xs", "--exclude-systems", metavar="sys1,[sys2[,...]]",
                   default=[], action=CombinationArgument,
                   help="""Exclude builds which combine this item with any of the
                   following systems.""")
    g.add_argument("-is", "--include-systems", metavar="sys1,[sys2[,...]]",
                   default=[], action=CombinationArgument,
                   help="""Include only builds which combine this item with any
                   of the following systems.""")

    g.add_argument("-xa", "--exclude-architectures", metavar="arch1,[arch2[,...]]",
                   default=[], action=CombinationArgument,
                   help="""Exclude builds which combine this item with any of the
                   following architectures.""")
    g.add_argument("-ia", "--include-architectures", metavar="arch1,[arch2[,...]]",
                   default=[], action=CombinationArgument,
                   help="""Include only builds which combine this item with any of the
                   following architectures.""")

    g.add_argument("-xc", "--exclude-compilers", metavar="comp1,[comp2[,...]]",
                   default=[], action=CombinationArgument,
                   help="""Exclude builds which combine this item with any of the
                   following compilers.""")
    g.add_argument("-ic", "--include-compilers", metavar="comp1,[comp2[,...]]",
                   default=[], action=CombinationArgument,
                   help="""Include only builds which combine this item with any of the
                   following compilers.""")

    g.add_argument("-xt", "--exclude-build-types", metavar="btype1,[btype2[,...]]",
                   default=[], action=CombinationArgument,
                   help="""Exclude builds which combine this item with any of the
                   following build types.""")
    g.add_argument("-it", "--include-build-types", metavar="btype1,[btype2[,...]]",
                   default=[], action=CombinationArgument,
                   help="""Exclude only builds which combine this item with any of the
                   following build types.""")

    g.add_argument("-xv", "--exclude-variants", metavar="var1,[var2[,...]]",
                   default=[], action=CombinationArgument,
                   help="""Exclude builds which combine this item with any of the
                   following variants.""")
    g.add_argument("-iv", "--include-variants", metavar="var1,[var2[,...]]",
                   default=[], action=CombinationArgument,
                   help="""Include only builds which combine this item with any of the
                   following variants.""")


def add_cflags(parser):
    g = parser.add_argument_group(
        'Flags: CMake cache variables, compiler flags and defines',
        description="""Can be given both at command-level and at item-level.
        When given at command level, these arguments apply to all builds.
        When given at item-level (eg compilers or build types), these arguments
        apply only to the particular item.""")
    g.add_argument("-T", "--toolchain", metavar='toolchain_file', type=str, default=None,
                   help="""Specify a cmake toolchain file.""")
    g.add_argument("-V", "--cmake-vars", default=[], action=FlagArgument,
                   help="""Add CMake cache variables.
                   Accepts a comma-separated list of CMake cache
                   variable definitions.
                   Multiple invokations of -V are possible, in which case
                   arguments will be appended and not overwritten.
                   To escape commas, use a backslash \\.""")
    g.add_argument("-D", "--defines", default=[], action=FlagArgument,
                   help="""Add preprocessor symbol definitions.
                   Accepts a comma-separated list of preprocessor macro
                   definitions, in either of the forms -D FOO or -D FOO=value.
                   Multiple invokations of -D are possible, in which case
                   arguments will be appended and not overwritten.
                   To escape commas, use a backslash \\.""")
    g.add_argument("-X", "--cxxflags", default=[], action=FlagArgument,
                   help="""Add C++ compiler flags.
                   Accepts a comma-separated list of C++ compiler flags.
                   These will be passed to cmake by appending to the
                   default initial value of CMAKE_CXX_FLAGS (taken from
                   CMAKE_CXX_FLAGS_INIT). cmany has flag aliases mapping
                   a single key to different compilers. Run `cmany help flags`
                   to get help about this.
                   Multiple invokations of -X are possible, in which case
                   arguments will be appended and not overwritten.
                   To escape commas, use a backslash \\.""")
    g.add_argument("-C", "--cflags", default=[], action=FlagArgument,
                   help="""Add C compiler flags.
                   Accepts a comma-separated list of C compiler flags.
                   These will be passed to cmake by appending to the
                   default initial value of CMAKE_C_FLAGS (taken from
                   CMAKE_C_FLAGS_INIT). cmany has flag aliases mapping
                   a single key to different compilers. Run `cmany help flags`
                   to get help about this.
                   Multiple invokations of -X are possible, in which case
                   arguments will be appended and not overwritten.
                   To escape commas, use a backslash \\.""")
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
    """a class to be used by argparse when parsing arguments which
    are compiler flags"""
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
class BuildItemArgument(argparse.Action):
    """a class to be used by argparse when parsing build item specifications.
    Note that prettyprint shows the specs wrong.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        li = getattr(namespace, self.dest)
        vli = build_item.BuildItem.parse_args(values)
        # clear the defaults from the list
        if not hasattr(parser, 'non_default_args'):
            parser.non_default_args = {}
        if parser.non_default_args.get(self.dest) is None:
            # util.logwarn("parsing: reset current li:", li)
            li = []
            parser.non_default_args[self.dest] = True
        # util.logwarn("parsing: current li:", li, " + ", vli)
        li += vli
        # util.logwarn("parsing: resulting li:", li)
        setattr(namespace, self.dest, li)


# -----------------------------------------------------------------------------
class CombinationArgument(argparse.Action):
    """parse combination arguments in order, putting them all into a single
    entry (combination_rules), which retains the original order. Maybe there's
    a cleverer way to do this but for now this is fast to implement."""
    def __call__(self, parser, namespace, values, option_string=None):
        # util.logwarn("parsing combinations: receive", self.dest, values)
        li = util.splitesc_quoted(values, ',')
        li = [util.unquote(item) for item in li]
        prev = getattr(namespace, self.dest)
        # util.logwarn("parsing combinations: receive", self.dest, values, ".... li", prev, "---->", prev + li)
        setattr(namespace, self.dest, prev + li)
        if not hasattr(namespace, 'combination_rules'):
            setattr(namespace, 'combination_rules', [])
        prev = getattr(namespace, 'combination_rules')

        if self.dest == 'exclude_builds':
            li = ('x', 'builds_any', li)
        elif self.dest == 'include_builds':
            li = ('i', 'builds_any', li)
        elif self.dest == 'exclude_builds_all':
            li = ('x', 'builds_all', li)
        elif self.dest == 'include_builds_all':
            li = ('i', 'builds_all', li)

        elif self.dest == 'exclude_systems':
            li = ('x', 'systems', li)
        elif self.dest == 'include_systems':
            li = ('i', 'systems', li)

        elif self.dest == 'exclude_architectures':
            li = ('x', 'architectures', li)
        elif self.dest == 'include_architectures':
            li = ('i', 'architectures', li)

        elif self.dest == 'exclude_compilers':
            li = ('x', 'compilers', li)
        elif self.dest == 'include_compilers':
            li = ('i', 'compilers', li)

        elif self.dest == 'exclude_build_types':
            li = ('x', 'build_types', li)
        elif self.dest == 'include_build_types':
            li = ('i', 'build_types', li)

        elif self.dest == 'exclude_variants':
            li = ('x', 'variants', li)
        elif self.dest == 'include_variants':
            li = ('i', 'variants', li)
        else:
            raise Exception("unoknown argument: " + self.dest)
        curr = prev
        curr.append(li)
        # util.logwarn("parsing combinations: receive", self.dest, values, ".... li", prev, "---->", curr)
        setattr(namespace, 'combination_rules', curr)
