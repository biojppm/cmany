from collections import OrderedDict as odict
import re

from . import util
from .named_item import NamedItem
from .build_flags import BuildFlags
from .combination_rules import CombinationRules


# some of parsing functions below are difficult; this is a debugging scaffold
_dbg_parse = False
def _dbg(fmt, *args):
    if not _dbg_parse: return
    print(fmt.format(*args))


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

    def is_trivial(self):
        if self.name != self.default_str():
            return False
        if not self.flags.empty():
            return False
        return True

    @staticmethod
    def trivial_item(items):
        return len(items) == 1 and items[0].is_trivial()

    @staticmethod
    def no_flags_in_collection(items):
        for i in items:
            if not i.flags.empty():
                return False
        return True

    def __init__(self, spec):
        self.full_specs = spec
        self.flag_specs = []
        self.refs = []
        self.combination_rules = CombinationRules([])
        self._resolved_references = False
        _dbg("\n\n{}: spec... 0: quoted={}", "<build item>", spec)
        spec = util.unquote(spec)
        _dbg("{}: spec... 1: unquoted={}", "<build item>", spec)
        spl = util.splitesc_quoted_first(spec, ':')
        _dbg("{}: spec... 2: splitted={}", "<build item>", spl)
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
        _dbg("{}: parsing flags... 0: rest={}", name, rest)
        spl = util.splitesc_quoted(rest, ' ')
        _dbg("{}: parsing flags... 1: split={}", name, spl)
        curr = ""
        for s in spl:
            _dbg("{}: parsing flags... 2  : {}", name, s)
            if s[0] != '@':
                curr += " " + s
                _dbg("{}: parsing flags... 2.1: append to curr: {}", name, curr)
            else:
                _dbg("{}: parsing flags... 2.2: it's a reference", name)
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
                tmp = BuildFlags('', **vars(args))
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
        if _dbg_parse: util.lognotice("parse_args 0: input=____{}____".format(v_))

        # remove start and end quotes if there are any
        v = v_
        if util.is_quoted(v_):
            v = util.unquote(v_)

        _dbg("parse_args 1: unquoted=____{}____", v)

        if util.has_interior_quotes(v):
            # this is the simple case: we assume everything is duly delimited
            vli = util.splitesc_quoted(v, ',')
            _dbg("parse_args 2: vli=__{}__", vli)
        else:
            # in the absence of interior quotes, parsing is more complicated.
            # Does the string have ':'?
            if v.find(':') == -1:
                # no ':' was found; a simple split will nicely do
                vli = v.split(',')
                _dbg("parse_args 3.1: vli=__{}__", vli)
            else:
                # uh oh. we have ':' in the string, but no quotes in it. This
                # means we have to do it the hard way. There's probably a
                # less hard and more robust way, but for now this is quick
                # enough to write.
                if _dbg_parse: print("parse_args 3.2: parsing without quotes...")
                vli = []
                i = 0
                while i < len(v):
                    _dbg("---\nparse_args 3.2.1: scanning at {}: __|{}|__", i, v[i:])
                    entry, i = __class__._consume_next_item(v, i)
                    _dbg("parse_args 3.2.2: i={} entry=__|{}|__ remainder=__|{}|___", i, entry, v[i:])
                    if entry:
                        vli.append(entry)
                        _dbg("parse_args 3.2.3: appended entry. vli={}", vli)
                rest = v[i:]
                if rest:
                    vli.append(rest)
                _dbg("parse_args 3.2.3: rest={} vli={}", rest, vli)
        if _dbg_parse: print("parse_args 4: vli=", vli)
        # unquote split elements
        vli = [util.unquote(v).strip(',') for v in vli]
        _dbg("parse_args 5: input=____{}____ output=__{}__", v_, vli)
        return vli

    @staticmethod
    def _consume_next_item(s, start_pos):
        _dbg("_cni: input_str=|{}|", s)
        # find the first colon-space
        icolon = s.find(': ', start_pos)
        if icolon == -1:
            _dbg("_cni: no colon. return full string[{}-{}]: |{}|", start_pos, len(s), s)
            # this is the last entry, so return the current string
            return s, len(input_str)
        _dbg("_cni: colon! string[{}:{}]=|{}|", start_pos, icolon, s[start_pos:icolon])
        icomma = s.rfind(',', start_pos, icolon)
        if icomma != -1:
            _dbg("_cni: comma behind! string[{}:{}]=|{}|", start_pos, icomma, s[start_pos:icomma])
            # there is a comma, so stop there
            return s[start_pos:icomma], icomma+1
        # there's no comma behind. So it starts at start_pos and extends
        # to the next entry. Now, where does the next entry start?
        _dbg("_cni: no comma behind. string[{}:{}]=|{}|", start_pos, icolon, s[start_pos:icolon])
        # Look ahead for a colon-space
        #beg = icolon + 2
        end = s.find(': ', icolon+2) # add 2 to skip the known ': ' at the start
        if end == -1:
            _dbg("_cni: this is the last entry. string[{}:{}]=|{}|", start_pos, len(s), s[start_pos:])
            return s[start_pos:], len(s)
        # we found a colon-space
        _dbg("_cni: colon ahead! string[{}:{}]=|{}|", start_pos, end, s[start_pos:end])
        #
        # now starting at the colon-space, look back for a comma
        icomma = s.rfind(',', start_pos, end)
        if icomma != -1:
            # there is a comma, so stop just before it
            end = icomma
            _dbg("_cni: comma before colon! string[{}:{}]=|{}|", start_pos, end, s[start_pos:end])
            return s[start_pos:end], end+1
        _dbg("_cni: no comma. string[{}:{}]=|{}|", start_pos, end, s[start_pos:end])
        return s[start_pos:end], end+1

    def save_config(self, yml_node):
        if not self.flags.empty():
            self.flags.save_config(yml_node)

    def load_config(self, yml_node):
        self.flags.load_config(yml_node)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class BuildItemCollection(odict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_names = odict()

    def __eq__(self, other):
        """code quality checkers complain that this class adds attributes
        without overriding __eq__. So just fool them!"""
        return super().__init__(other)

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
        # store the class name
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
