#!/usr/bin/env python3

import pycmake
from collections import OrderedDict as odict
import argparse
import sys


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Command line tool
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

cmds = odict([
    ('help', ['h']),
    ('configure', ['conf', 'c']),
    ('build', ['b']),
    ('install', ['i']),
])


def pycmake_main(in_args=None):
    '''Easily process several build trees of a CMake project'''
    if in_args is None: in_args = sys.argv[1:]
    p = argparse.ArgumentParser(prog='pycmake',
                                description=__doc__,
                                usage='%(prog)s [-h]',
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog=examples)
    sp = p.add_subparsers(help='')
    for cmd,aliases in cmds.items():
        cl = cmdclass(cmd)
        h = sp.add_parser(name=cmd, aliases=aliases,
                          help=cl.__doc__, description=cl.__doc__)
        cl().add_args(h)
        def exec_cmd(args, cmd_class = cl):
            obj = cmd_class()
            proj = obj.proj(args)
            obj._exec(proj, args)
        h.set_defaults(func=exec_cmd)
    args = p.parse_args(in_args)
    if not hasattr(args, 'func'):
        argerror('missing subcommand')
    args.func(args)


def cmdclass(cmd_name):
    return getattr(sys.modules[__name__], cmd_name)


def argerror(*msg_args):
    print(*msg_args, '\n')
    pycmake_main(['-h'])
    exit(1)


def cslist(arg):
    '''transform comma-separated arguments into a list of strings'''
    return arg.split(',')


# -----------------------------------------------------------------------------
class cmdbase:
    '''base class for commands'''
    def add_args(self, parser):
        '''add arguments to a command parser'''
        pass
    def proj(self, args):
        print(args)
        '''create a project given the configuration.'''
        return ProjectConfig(**vars(args))
    def _exec(self, proj, args):
        raise Exception('never call the base class method. Implement this in derived classes')


class projcmd(cmdbase):
    '''a command which refers to a project'''
    def add_args(self, parser):
        parser.add_argument("proj-dir", nargs="?", default=".",
                            help="""the directory where CMakeLists.txt is located. An empty argument
                            will default to the current directory ie, \".\". Passing a directory
                            which does not contain a CMakeLists.txt will cause an error.""")
        parser.add_argument("--build-dir", default="./build",
                            help="set the build root (defaults to ./build)")
        parser.add_argument("--install-dir", default="./install",
                            help="set the install root (defaults to ./install)")
        parser.add_argument("-j", "--jobs", default=cpu_count(),
                            help="""build with the given number of parallel jobs
                            (defaults to %(default)s on this machine).""")
        parser.add_argument("-G", "--generator", default=Generator.default_str(),
                            help="set the cmake generator (on this machine, defaults to \"%(default)s\")")
        parser.add_argument("-C", "--compiler-flags", default=Generator.default_str(),
                            help="set the cmake generator (on this machine, defaults to \"%(default)s\")")


class selectcmd(projcmd):
    '''a command which selects several builds'''
    def add_args(self, parser):
        super().add_args(parser)
        g = parser.add_argument_group(title="Selecting the builds")
        g.add_argument("-t", "--build-types", metavar="type1,type2,...", default=["Release"], type=cslist,
                       help="""restrict actions to the given build types.
                       Defaults to \"%(default)s\".""")
        g.add_argument("-c", "--compilers", metavar="compiler1,compiler2,...",
                       default=[Compiler.default_str()], type=cslist,
                       help="""restrict actions to the given compilers.
                       Defaults to CMake's default compiler, \"%(default)s\" on this system.""")
        g.add_argument("-s", "--systems", metavar="os1,os2,...", default=[System.default_str()], type=cslist,
                       help="""(WIP) restrict actions to the given operating systems.
                       Defaults to the current system, \"%(default)s\".
                       This feature requires os-specific toolchains and is currently a
                       work-in-progress.""")
        g.add_argument("-a", "--architectures", metavar="arch1,arch2,...",
                       default=[Architecture.default_str()], type=cslist,
                       help="""(WIP) restrict actions to the given processor architectures.
                       Defaults to CMake's default architecture, \"%(default)s\" on this system.
                       This feature requires os-specific toolchains and is currently a
                       work-in-progress.""")
        g.add_argument("-v", "--variants", metavar="variant1,variant2,...", default=[], type=cslist,
                       help="""(WIP) restrict actions to the given variants.
                       This feature is currently a work-in-progress.""")


class help(projcmd):
    '''get help on a particular subcommand or topic'''
    def add_args(self, parser):
        parser.add_argument('subcommand', default="")
    def _exec(self, proj, args):
        if not hasattr(args, 'subcommand'):
            pycmake_main(['-h'])
        else:
            sc = cmds.get(args.subcommand)
            if sc is not None:
                pycmake_main([sc, '-h'])
            else:
                subtopic = help_topics.get(args.subcommand)
                if subtopic is None:
                    argerror("unknown subcommand:", args.subcommand)
                if isinstance(subtopic, str):
                    print(subtopic)
                else:
                    h = subtopic()
                    print(h)


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


# ------------------------------------------------------------------------------


# to update the examples in a Markdown file, pipe the help through sed:
# sed 's:^#\ ::g' | sed 's:^\$\(\ .*\):\n```\n$ \1\n```:g'
examples = '''
-----------------------------
Some examples:

# Configure and build a CMakeLists.txt project located on the folder above
# the current one. The build trees will be placed in separate folders under
# a folder named "build" located on the current folder. Likewise, the installation
# prefix will be set to a sister folder named "install". A c++ compiler will
# be selected from the system, and the CMAKE_BUILD_TYPE will be set to Release.
$ %(prog)s build ..

# Same as above, but now look for CMakeLists.txt on the current dir.
$ %(prog)s build .

# Same as above: like with cmake, omitting the project dir defaults will cause
# searching for CMakeLists.txt on the current dir.
$ %(prog)s build

# Same as above: 'b' can be used as an alias to 'install'.
$ %(prog)s b

# Same as above, and additionally install. 'i' can be used as an alias to 'install'.
$ %(prog)s i

# Only configure; do not build, do not install. 'conf' and 'c' are aliases to 'configure'.
$ %(prog)s c

# Build only the Debug build type.
$ %(prog)s b -t Debug

# Build both Debug and Release build types (resulting in 2 build trees).
$ %(prog)s b -t Debug,Release

# Build using both clang++ and g++ (2 build trees).
$ %(prog)s b -c clang++,g++

# Build using both clang++,g++ and in Debug,Release modes (4 build trees).
$ %(prog)s b -c clang++,g++ -t Debug,Release

# Build using clang++,g++,icpc in Debug,Release,MinSizeRel modes (9 build trees).
$ %(prog)s b -c clang++,g++,icpc -t Debug,Release,MinSizeRel
'''

help_topics = {
    'variants':'''
help on variants
''',

    'compiler_flags':'''
help on preset compiler flags
''',

    'visual_studio':'''
visual studio topic help
''',
}


# -----------------------------------------------------------------------------

if __name__ == "__main__":

    pycmake_main(sys.argv[1:])
