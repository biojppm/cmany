import sys
import os.path as osp
from collections import OrderedDict as odict
from . import util

from ruamel import yaml
from ruamel.yaml.comments import CommentedMap as CommentedMap

if yaml.version_info < (0, 15):
    raise Exception("cmany now requires ruamel.yaml>=0.15.0")

# -----------------------------------------------------------------------------
SHARE_DIR = osp.abspath(
    osp.join(
        osp.dirname(osp.dirname(sys.executable)),
        'share', 'c4', 'cmany'
    )
)
CONF_DIR = osp.join(SHARE_DIR, 'conf')
DOC_DIR = osp.join(SHARE_DIR, 'doc')
USER_DIR = osp.expanduser("~/.cmany/")

# maybe cmany is not installed. Then it must be a source distribution.
if not osp.exists(SHARE_DIR):
    SHARE_DIR = osp.abspath(osp.join(osp.dirname(__file__), "../../.."))
    CONF_DIR = osp.join(SHARE_DIR, 'conf')
    DOC_DIR = osp.join(SHARE_DIR, 'doc/_build/text')

assert osp.exists(SHARE_DIR), "cmany: share dir not found: {}".format(SHARE_DIR)
assert osp.exists(CONF_DIR), "cmany: conf dir not found: {}".format(CONF_DIR)
assert osp.exists(DOC_DIR), "cmany: doc dir not found: {}".format(DOC_DIR)
assert osp.exists(USER_DIR), "cmany: user dir not found: {}".format(USER_DIR)

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Configs:

    @staticmethod
    def load_seq(file_seq):
        curr = None
        for fn in file_seq:
            if not osp.exists(fn):
                continue
            if curr is None:
                curr = Configs()
                curr.load(fn)
            else:
                tmp = Configs()
                tmp.load(fn)
                curr.merge_from(tmp)
        return curr

    def __init__(self):
        self._load_yml("""\
project: {}
config: {}
flag_aliases: {}
""")

    def _load_yml(self, yml):
        YAML = yaml.YAML()
        dump = YAML.load(yml)
        dump = odict(dump)
        for i in ('project', 'config', 'flag_aliases'):
            if dump.get(i) is None:
                dump[i] = CommentedMap()
            setattr(self, i, dump[i])
        self._dump = dump
        from . import flags as c4flags
        self.flag_aliases = c4flags.FlagAliases(yml=dump.get('flag_aliases', CommentedMap()))

    def load(self, file=None, text=None):
        """file or text"""
        if file == text:
            raise Exception("either file or text")
        if file:
            with open(file, "r") as f:
                text = f.read()
        self._load_yml(text)

    def save(self, filename):
        raise Exception("not implemented")

    @staticmethod
    def _merge(dict_recv, dict_send):
        #"""http://stackoverflow.com/questions/38987/how-to-merge-two-python-dictionaries-in-a-single-expression"""
        #z = dict_recv.copy()
        #z.update(dict_send)
        z = util.nested_merge(dict_recv, dict_send)
        return z

    def merge_from(self, other):
        for k in (list(self._dump.keys()) + list(other._dump.keys())):
            dst = self._dump.get(k)
            src = other._dump.get(k)
            def is_dict(d):
                return isinstance(d, dict) or isinstance(d, odict) or isinstance(d, CommentedMap)
            if (dst is not None and src is not None):
                if is_dict(dst) and is_dict(src):
                    self._dump[k] = __class__._merge(dst, src)
                elif is_dict(dst) or is_dict(src):
                    raise Exception("cannot merge when only one is a dict")
                else:
                    self._dump[k] = other._dump[k]
            elif src is not None:
                self._dump[k] = other._dump[k]
        self.flag_aliases = self.flag_aliases.merge_from(other.flag_aliases)

    def get_val(self, name_sub, where=None):
        if where is None:
            where = self._dump
        elms = name_sub.split('.')
        curr = where
        for e in elms:
            if curr.get(e) is not None:
                curr = curr.get(e)
            else:
                return None
        return curr

    def set_val(self, name_sub, value, where=None):
        spl = name_sub.split(".")
        child = spl[-1]
        seq = spl[:-1]
        parent_name = ".".join(seq)
        parent = self.get_val(parent_name, where)
        if parent is None:
            curr = self._dump
            for c in seq:
                ch = curr.get(c)
                if ch is None:
                    curr[c] = CommentedMap()
                    curr = curr[c]
            parent = curr
        #
        if isinstance(value, str) or isinstance(value, int) or isinstance(value, float) or isinstance(value, list):
            parent[child] = value
        elif isinstance(value, dict) or isinstance(value, odict):
            parent[child] = CommentedMap(value)

    def append_val(self, name_sub, value, where=None):
        oldval = self.get_val(name_sub, where)
        if not isinstance(oldval, list):
            raise Exception("WTF?")
        value = oldval + value
        self.set_val(name_sub, value, where)
