#!/usr/bin/env python3

import sys
import argcomplete

from collections import OrderedDict as odict

from c4.cmany.project import Project as Project
from c4.cmany import args as c4args
from c4.cmany import help as c4help


cmds = odict([
    ('help', ['h']),
    ('configure', ['c']),
    ('build', ['b']),
    ('install', ['i']),
    ('run', ['r']),
    ('show_vars', ['sv']),
    ('show_builds', ['sb']),
    ('show_build_names', ['sn']),
    ('show_build_dirs', ['sd']),
    ('show_targets', ['st']),
    ('create_proj', []),
    ('export_vs', []),
])


def cmany_main(in_args=None):
    if in_args is None:
        in_args = sys.argv[1:]
    mymod = sys.modules[__name__]
    parser = c4args.setup(cmds, mymod)
    argcomplete.autocomplete(parser)
    args = c4args.parse(parser, in_args)
    if args:
        args.func(args)


# -----------------------------------------------------------------------------
class cmdbase:
    '''base class for commands'''
    def add_args(self, parser):
        '''add arguments to a command parser'''
        pass
    def proj(self, args):
        return None
    def _exec(self, proj, args):
        assert False, 'never call the base class method. Implement this in derived classes'


class help(cmdbase):
    """get help on a particular subcommand or topic"""
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
                subtopic = c4help.topics.get(args.subcommand_or_topic)
                if subtopic is None:
                    msg = ("{} is not a subcommand or topic.\n" +
                           "Available subcommands are: {}\n" +
                           "Available help topics are: {}\n")
                    print(msg.format(args.subcommand_or_topic,
                                     ', '.join(cmds.keys()),
                                     ', '.join(c4help.topics.keys())))
                    exit(1)
                else:
                    print(subtopic.txt)


class projcmd(cmdbase):
    '''a command which refers to a project'''
    def proj(self, args):
        '''create a project given the configuration.'''
        return Project(**vars(args))
    def add_args(self, parser):
        super().add_args(parser)
        c4args.add_proj(parser)
        c4args.add_bundle_flags(parser)


class selectcmd(projcmd):
    '''a command which selects several builds'''
    def add_args(self, parser):
        super().add_args(parser)
        c4args.add_select(parser)


class configure(selectcmd):
    '''configure the selected builds'''
    def _exec(self, proj, args):
        proj.configure()
    def add_args(self, parser):
        super().add_args(parser)


class build(selectcmd):
    '''build the selected builds, configuring before if necessary'''
    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument('target', default=[], nargs='*',
                            help="""specify a subset of targets to build""")
    def _exec(self, proj, args):
        proj.build()


class install(selectcmd):
    '''install the selected builds, building before if necessary'''
    def _exec(self, proj, args):
        proj.install()


class run(selectcmd):
    '''run a command in each build directory'''
    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument('command', default="",
                            help="""command to be run in each build directory""")
    def _exec(self, proj, args):
        proj.run_cmd(args.command)


class show_vars(selectcmd):
    '''show the value of certain CMake cache vars'''
    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument('var_names', default="", nargs='+')
    def _exec(self, proj, args):
        proj.show_vars(args.var_names)


class show_build_names(selectcmd):
    '''show the build names'''
    def _exec(self, proj, args):
        proj.show_build_names()


class show_build_dirs(selectcmd):
    '''show the build directories'''
    def _exec(self, proj, args):
        proj.show_build_dirs()


class show_builds(selectcmd):
    '''show the build properties'''
    def _exec(self, proj, args):
        proj.show_builds()


class show_targets(selectcmd):
    '''show the targets of a single build'''
    def _exec(self, proj, args):
        proj.show_targets()


class create_proj(selectcmd):
    '''create cmany.yml alongside CMakeLists.txt to hold project-settings
    '''
    def _exec(self, proj, args):
        proj.create_proj()


class export_vs(selectcmd):
    '''create CMakeSettings.json, a VisualStudio 2015+ compatible file
    outlining the project builds
    '''
    def _exec(self, proj, args):
        proj.export_vs()


# -----------------------------------------------------------------------------

if __name__ == "__main__":

    cmany_main(sys.argv[1:])
