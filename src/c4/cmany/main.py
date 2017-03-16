#!/usr/bin/env python3

import sys
import pprint
from collections import OrderedDict as odict

from . import cmanys as cmany, util, args as c4args, help as c4help


cmds = odict([
    ('help', ['h']),
    ('configure', ['c']),
    ('build', ['b']),
    ('install', ['i']),
    ('show_vars', []),
    ('show_builds', []),
    ('show_targets', []),
    ('create', []),
    ('export_vs', []),
])


def cmany_main(in_args=None):
    if in_args is None: in_args = sys.argv[1:]
    mymod = sys.modules[__name__]
    parser = c4args.setup(cmds, mymod)
    args = c4args.parse(parser, in_args)
    #
    if args.show_args or args.show_args_only:
        pprint.pprint(vars(args), indent=4)
        if args.show_args_only:
            return
    if args.dump_help_topics:
        dump_help_topics()
    #
    args.func(args)


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
        return cmany.ProjectConfig(**vars(args))
    def add_args(self, parser):
        super().add_args(parser)
        c4args.add_proj(parser)
        c4args.add_cflags(parser)


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


class show_vars(selectcmd):
    '''show the value of certain CMake cache vars'''
    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument('var_names', default="", nargs='+')

    def _exec(self, proj, args):
        proj.showvars(args.var_names)


class show_builds(selectcmd):
    '''show the build names'''
    def _exec(self, proj, args):
        proj.showbuilds()


class show_targets(selectcmd):
    '''show the targets of a single build'''
    def _exec(self, proj, args):
        proj.showtargets()


class create(selectcmd):
    '''create cmany.yml alongside CMakeLists.txt to hold project-settings
    '''
    def _exec(self, proj, args):
        raise Exception("not implemented")


class export_vs(selectcmd):
    '''create CMakeSettings.json, a VisualStudio 2015+ compatible file
    outlining the project builds
    '''
    def _exec(self, proj, args):
        proj.create_projfile()


# -----------------------------------------------------------------------------
def dump_help_topics():
    for t, _ in c4help.topics.items():
        print(t)
        txt = util.runsyscmd([sys.executable, sys.modules[__name__].__file__,
                              'help', t], echo_cmd=False, capture_output=True)
        print(txt)

# -----------------------------------------------------------------------------

if __name__ == "__main__":

    cmany_main(sys.argv[1:])
