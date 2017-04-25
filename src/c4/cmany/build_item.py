from collections import OrderedDict as odict
import re

from . import util
from .named_item import NamedItem
from .build_flags import BuildFlags
from .combination_rules import CombinationRules


# -----------------------------------------------------------------------------
class BuildItem(NamedItem):
    """A base class for build items."""

    @staticmethod
    def create(map_of_class_name_to_tuple_of_class_and_specs):
        items = BuildItemCollection()
        for cls_name, (cls, spec_list) in map_of_class_name_to_tuple_of_class_and_specs.items():
            if isinstance(spec_list, str):
                spec_list = util.splitesc_quoted(spec_list, ',')
            for s in spec_list:
                items.add_build_item(cls(s))
        items.resolve_references()
        return items

    def __init__(self, spec):
        self.full_specs = spec
        self.flag_specs = []
        self.refs = []
        self.combination_rules = CombinationRules([])
        self._resolved_references = False
        spec = util.unquote(spec)
        spl = spec.split(':')
        if len(spl) == 1:
            name = spec
            self.flags = BuildFlags(name)
            super().__init__(name)
            return
        name = spl[0]
        rest = spl[1]
        # super().__init__(name)  # DON'T!!! will overwrite
        self.name = name
        self.flags = BuildFlags(name)
        spl = util.splitesc_quoted(rest, ' ')
        curr = ""
        for s in spl:
            if s[0] != '@':
                curr += " " + s
            else:
                self.refs.append(s[1:])
                if curr:
                    self.flag_specs.append(curr)
                    curr = ""
                self.flag_specs.append(s)
        if curr:
            self.flag_specs.append(curr)

    def resolve_references(self, item_collection):
        if self._resolved_references:
            return
        for s_ in self.flag_specs:
            s = s_.lstrip()
            if s[0] == '@':
                refname = s[1:]
                r = item_collection.lookup_build_item(refname, self.__class__)
                if self.name in r.refs:
                    msg = "circular references found in {} definitions: '{}'x'{}'"
                    raise Exception(msg.format(self.__class__.__name__, self.name, r.name))
                if not r._resolved_references:
                    r.resolve_references(item_collection)
                self.flags.append_flags(r.flags, append_to_name=False)
            else:
                import argparse
                from . import args as c4args
                parser = argparse.ArgumentParser()
                c4args.add_bundle_flags(parser)
                ss = util.splitesc_quoted(s, ' ')
                args = parser.parse_args(ss)
                tmp = BuildFlags('', None, **vars(args))
                self.flags.append_flags(tmp, append_to_name=False)
                cr = []
                if hasattr(args, 'combination_rules'):
                    cr = getattr(args, 'combination_rules')
                self.combination_rules = CombinationRules(cr)
        self._resolved_references = True

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

    def save_config(self, yml_node):
        if yml_node.get('flags') is None:
            yml_node['flags'] = type(yml_node)()
        self.flags.save_config(yml_node['flags'])

    def load_config(self, yml_node):
        if yml_node.get('flags'):
            self.flags.load_config(yml_node['flags'])


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class BuildItemCollection(odict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_names = odict()

    def add_build_item(self, item):
        # convert the class name to snake case and append s for plural
        # eg Variant-->variants and BuildType --> build_types
        # http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
        cls = item.__class__
        cls_name = cls.__name__
        cls_name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls_name)
        cls_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', cls_name)
        cls_name = cls_name.lower() + 's'
        # add the item to the list of the class name
        if not self.get(cls_name):
            self[cls_name] = []
        self[cls_name].append(item)
        # store the
        if not hasattr(self, 'collections'):
            setattr(self, 'collections', [])
        if not cls_name in self.collections:
            self.collections.append(cls_name)
        # add the object to a map to accelerate lookups by item name
        if not self.item_names.get(item.name):
            self.item_names[item.name] = []
        self.item_names[item.name].append(item)

    def lookup_build_item(self, item_name, item_cls=None):
        items = self.item_names[item_name]
        # first look for items with the same class and same name
        for i in items:
            if i.name == item_name and i.__class__ == item_cls:
                return i
        # now look for just same name
        for i in items:
            if i.name == item_name:
                return i
        # at least one must be found
        msg = "item not found: {} (class={})".format(item_name,
                                                     item_cls.__name__)
        raise Exception(msg)

    def resolve_references(self):
        for c in self.collections:
            for item in self[c]:
                item.resolve_references(self)
