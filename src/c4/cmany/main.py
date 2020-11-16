#!/usr/bin/env python3

import sys
import argcomplete

from collections import OrderedDict as odict

from c4.cmany.project import Project as Project
from c4.cmany import args as c4args
from c4.cmany import help as c4help
from c4.cmany import err


cmds = odict([
    ('help', ['h']),
    ('configure', ['c']),
    ('reconfigure', ['rc']),
    ('build', ['b']),
    ('build_file', ['bf']),
    ('rebuild', ['rb']),
    ('install', ['i']),
    ('reinstall', ['ri']),
    ('run', ['r']),
    ('show_vars', ['sv']),
    ('show_builds', ['sb']),
    ('show_build_names', ['sn']),
    ('show_build_dirs', ['sd']),
    ('show_targets', ['st']),
    ('create_proj', ['cp']),
    ('export_compile_commands', ['xc']),
    ('export_vs', []),
])


def cmd_abbrevs():
    for k, v in cmds.items():
        if v:
            yield (f"{k}, " + ', '.join(cmds[k]))
        else:
            yield k


def cmany_main(in_args=None):
    if in_args is None:
        in_args = sys.argv[1:]
    in_args = c4args.merge_envargs(cmds, in_args)
    mymod = sys.modules[__name__]
    parser = c4args.setup(cmds, mymod)
    # to enable autocomplete:
    # eval "$(register-python-argcomplete cmany)"
    # see https://stackoverflow.com/questions/14597466/custom-tab-completion-in-python-argparse
    argcomplete.autocomplete(parser)
    try:
        args = c4args.parse(parser, in_args)
        if args:
            args.func(args)
        return 0
    except err.Error as e:
        print(e, file=sys.stderr)
        return 1


# -----------------------------------------------------------------------------
class cmdbase:
    """base class for commands"""
    def add_args(self, parser):
        """add arguments to a command parser"""
        pass
    def proj(self, args):
        """create a project given the configuration."""
        return None
    def _exec(self, proj, args):
        assert False, 'never call the base class method. Implement this in derived classes'


class help(cmdbase):
    """get help on a particular subcommand or topic"""
    def add_args(self, parser):
        parser.add_argument('subcommand_or_topic', default="", nargs='?')
    def _exec(self, proj, args):
        sct = args.subcommand_or_topic.lower()
        if not sct:
            cmany_main(['-h'])
        else:
            sc = cmds.get(sct)
            # is it a subcommand?
            if sc is not None:
                self._show(sct)
            else:
                # is it a subcommand alias?
                sc = None
                for c, aliases in cmds.items():
                    if sct in aliases:
                        sc = c
                        break
                if sc is not None:
                    self._show(sc)
                else:
                    # is it a topic?
                    subtopic = c4help.topics.get(sct)
                    if subtopic is not None:
                        print(subtopic.txt)
                    else:
                        _ind = '    '
                        _indnl = '\n' + _ind
                        _cmds = _ind + _indnl.join(cmd_abbrevs())
                        _topics = _ind + _indnl.join(c4help.topics.keys())
                        msg = (f"Error: {args.subcommand_or_topic} is not a subcommand or topic.\n" +
                               f"\nAvailable subcommands are:\n{_cmds}\n" +
                               f"\nAvailable help topics are:\n{_topics}\n")
                        exit(msg)
    def _show(self, subcommand):
        import textwrap
        import re
        mymod = sys.modules[__name__]
        if hasattr(mymod, subcommand):
            cls = getattr(mymod, subcommand)
            sctxt = "/".join([subcommand] + cmds[subcommand])
            block = re.sub("\n", " ", cls.__doc__)
            block = re.sub(r"\ +", " ", block)
            block = textwrap.fill(block, 60)
            sep = "--" * 20 + "\n"
            print(f"{sep}cmany {sctxt}\n{sep}\n{block}\n")
        cmany_main([subcommand, '-h'])


# -----------------------------------------------------------------------------
class globcmd(cmdbase):
    """a command applying to a python glob pattern matching build directory names"""
    def proj(self, args):
        return Project(**vars(args))
    def add_args(self, parser):
        super().add_args(parser)
        c4args.add_glob(parser)


# -----------------------------------------------------------------------------
class projcmd(cmdbase):
    """a command which refers to a project"""
    def proj(self, args):
        return Project(**vars(args))
    def add_args(self, parser):
        c4args.add_proj(parser)
        c4args.add_bundle_flags(parser)


class selectcmd(projcmd):
    """a command which selects several builds"""
    def add_args(self, parser):
        super().add_args(parser)
        c4args.add_select(parser)


class configure(selectcmd):
    """configure the selected builds"""
    def _exec(self, proj, args):
        proj.configure()


class reconfigure(globcmd):
    """reconfigure the selected builds, selecting by name using a python glob pattern"""
    def _exec(self, proj, args):
        proj.reconfigure()


class build(selectcmd):
    """build the selected builds, configuring before if necessary"""
    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument('target', default=[], nargs='*',
                            help="""specify a subset of targets to build""")
    def _exec(self, proj, args):
        proj.build()


class install(selectcmd):
    """install the selected builds, building before if necessary"""
    def _exec(self, proj, args):
        proj.install()


class build_file(globcmd):
    """compile the given source files"""
    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument('target', nargs=1,
                            help="""the target to which the source files belong""")
        parser.add_argument('files', default=[], nargs='*',
                            help="""the files to compile, relative to the CMakeLists.txt root dir""")
    def _exec(self, proj, args):
        proj.build_files(args.target, args.files)


class rebuild(globcmd):
    """rebuild the selected builds, selecting by name using a python glob pattern"""
    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument('target', default=[], nargs='*',
                            help="""specify a subset of targets to build""")
    def _exec(self, proj, args):
        proj.rebuild()


class reinstall(globcmd):
    """rebuild the selected builds, selecting by name using a python glob pattern"""
    def _exec(self, proj, args):
        proj.reinstall()


class run(selectcmd):
    """run a command in each build directory"""
    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument('command', nargs='+',
                            help="""command to be run in each build directory""")
        parser.add_argument('-np', '--not-posix', action="store_true",
                            help="""do not use posix mode if splitting the initial string""")
        parser.add_argument('-nc', '--no-check', action="store_true",
                            help="""do not use check the error status of the command""")
        parser.add_argument('-tg', '--target', nargs="+",
                            help="""build these targets before running the command""")
    def _exec(self, proj, args):
        if len(args.target) > 0:
            proj.build()  # targets are set
        proj.run_cmd(args.command, posix_mode=not args.not_posix, check=not args.no_check)


class show_vars(selectcmd):
    """show the value of certain CMake cache vars"""
    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument('var_names', default="", nargs='+')
    def _exec(self, proj, args):
        proj.show_vars(args.var_names)


class show_build_names(selectcmd):
    """show the build names"""
    def _exec(self, proj, args):
        proj.show_build_names()


class show_build_dirs(selectcmd):
    """show the build directories"""
    def _exec(self, proj, args):
        proj.show_build_dirs()


class show_builds(selectcmd):
    """show the builds and their properties"""
    def _exec(self, proj, args):
        proj.show_builds()


class show_targets(selectcmd):
    """show the targets of a single build"""
    def _exec(self, proj, args):
        proj.show_targets()


# -----------------------------------------------------------------------------
class create_proj(selectcmd):
    """[EXPERIMENTAL] create cmany.yml alongside CMakeLists.txt to hold project-settings"""
    hidden = True
    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument('-o', '--output-file', default="cmany.yml",
                            help="""file where the project should be written.
                            Accepts relative or absolute paths. Relative paths
                            are taken from the current working directory.""")
    def _exec(self, proj, args):
        proj.create_proj()


class export_compile_commands(selectcmd):
    """[EXPERIMENTAL] create a compile_commands.json in each build dir, for cases (such as VS)
    _even if_ the build's generator is unable to export one. This requires
    creating a dummy build dir using the Ninja generator, from where
    compile_commands.json is copied to the build's dir."""
    def _exec(self, proj, args):
        proj.export_compile_commands()


class export_vs(selectcmd):
    """[EXPERIMENTAL] create CMakeSettings.json, a VisualStudio 2015+ compatible file
    outlining the project builds
    """
    def _exec(self, proj, args):
        proj.export_vs()


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    cmany_main(sys.argv[1:])
