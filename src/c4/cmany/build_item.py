
from . import util
from .named_item import NamedItem
from .build_flags import BuildFlags


# -----------------------------------------------------------------------------
class BuildItem(NamedItem):
    """A base class for build items."""

    def __init__(self, name_or_spec):
        name_or_spec = util.unquote(name_or_spec)
        self.name = name_or_spec
        self.flags = BuildFlags(name_or_spec)
        self.full_specs = name_or_spec
        self.flag_specs = []
        #
        self.parse_specs(name_or_spec)

    def parse_specs(self, spec, parse_flags=True):
        spl = spec.split(':')
        if len(spl) == 1:
            return
        self.name = spl[0]
        self.flag_specs = util.splitesc_quoted(spl[1], ' ')
        if parse_flags:
            from . import args as c4args
            import argparse
            parser = argparse.ArgumentParser()
            c4args.add_bundle_flags(parser)
            args = parser.parse_args(self.flag_specs)
            self.flags = BuildFlags(self.name, None, **vars(args))

    @staticmethod
    def parse_args(v_):
        """parse comma-separated build item specs from the command line.

        An individual build item spec can have any of the following forms:
          * name
          * 'name:'
          * "name:"
          * 'name: <flag_specs...>'
          * "name: <flag_specs...>"
        So for example, any of these could be valid input to this function:
          * foo,bar
          * foo,'bar: -X "-a" "-b" (etc)'
          * foo,"bar: -X '-a' '-b' (etc)"
          * 'foo: -DTHIS_IS_FOO -X "-a"','bar: -X "-a" "-b" (etc)'
          * 'foo: -DTHIS_IS_FOO -X "-a"',bar
          * etc

        In some cases the shell (or argparse? or what?) removes quotes, so we
        have to deal with that too.
        """

        #util.lognotice("parse_args 0: input=____{}____".format(v_))

        # remove start and end quotes if there are any
        v = v_
        if util.is_quoted(v_):
            v = util.unquote(v_)

        # print("parse_args 1: unquoted=____{}____".format(v))

        if util.has_interior_quotes(v):
            # this is the simple case: we assume everything is duly delimited
            vli = util.splitesc_quoted(v, ',')
            # print("parse_args 2: vli=__{}__".format(vli))
        else:
            # in the absence of interior quotes, parsing is more complicated.
            # Does the string have ':'?
            if v.find(':') == -1:
                # no ':' was found; a simple split will nicely do
                vli = v.split(',')
                # print("parse_args 3.1: vli=__{}__".format(vli))
            else:
                # uh oh. we have ':' in the string, but no quotes in it. This
                # means we have to do it the hard way. There's probably a
                # less hard way, but for now this is short enough.
                # print("parse_args 3.2: parsing manually...")
                vli = []
                withc = False
                b = 0
                lastcomma = -1
                for i, c in enumerate(v):
                    if c == ',':
                        if not withc:
                            vli.append(v[b:i])
                            b = i + 1
                        # print("parse_args 3.2.1:  ','@ i={}:  v[b:i]={} vli={}".format(i, v[b:i], vli))
                        lastcomma = i
                    elif c == ':':
                        if not withc:
                            withc = True
                        else:
                            vli.append(v[b:(lastcomma + 1)])
                        b = lastcomma + 1
                        # print("parse_args 3.2.2:  ':'@ i={}:  v[b:i]={} vli={}".format(i, v[b:i], vli))
                rest = v[b:]
                if rest:
                    vli.append(rest)
                # print("parse_args 3.2.3: rest={} vli={}".format(rest, vli))

        # print("parse_args 4: vli=", vli)
        # unquote split elements
        vli = [util.unquote(v).strip(',') for v in vli]
        # util.logdone("parse_args 4: input=____{}____ output=__{}__".format(v_, vli))
        return vli
