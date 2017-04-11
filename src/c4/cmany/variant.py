import argparse

from .build_item import BuildItem
from .build_flags import BuildFlags
from . import util
from . import args as c4args


# -----------------------------------------------------------------------------
class Variant(BuildItem):
    """for variations in build flags"""

    @staticmethod
    def default():
        return Variant('none')

    @staticmethod
    def create(spec_list):
        if isinstance(spec_list, str):
            spec_list = util.splitesc_quoted(spec_list, ',')
        variants = []
        for s in spec_list:
            v = Variant(s)
            variants.append(v)
        for s in variants:
            s.resolve_references(variants)
        return variants

    def __init__(self, spec):
        self.full_specs = spec
        self.flag_specs = []
        self.refs = []
        self._resolved_references = False
        spec = util.unquote(spec)
        spl = spec.split(':')
        if len(spl) == 1:
            name = spec
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

    def resolve_references(self, variants):
        if self._resolved_references:
            return
        def _find_variant(name):
            for v in variants:
                if v.name == name:
                    return v
            raise Exception("variant '{}' not found in {}".format(name, variants))
        for s_ in self.flag_specs:
            s = s_.lstrip()
            if s[0] == '@':
                refname = s[1:]
                r = _find_variant(refname)
                if self.name in r.refs:
                    msg = "circular references found in variant definitions: '{}'x'{}'"
                    raise Exception(msg.format(self.name, r.name))
                if not r._resolved_references:
                    r.resolve_all(variants)
                self.flags.append_flags(r.flags, append_to_name=False)
            else:
                parser = argparse.ArgumentParser()
                c4args.add_bundle_flags(parser)
                ss = util.splitesc_quoted(s, ' ')
                args = parser.parse_args(ss)
                tmp = BuildFlags('', None, **vars(args))
                self.flags.append_flags(tmp, append_to_name=False)
        self._resolved_references = True
