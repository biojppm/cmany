import os.path as osp

CONF_DIR = osp.join(osp.dirname(__file__), "conf")
# maybe cmany is not installed. Then it must be a source distribution.
if not osp.exists(CONF_DIR):
    CONF_DIR = osp.abspath(osp.join(osp.dirname(__file__), "../../../conf"))
    assert osp.exists(CONF_DIR)

USER_DIR = osp.expanduser("~/.cmany/")


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class Configs:

    @staticmethod
    def load(file_seq=None):
        curr = None
        for fn in file_seq:
            if not osp.exists(fn):
                continue
            if curr is None:
                curr = Configs(fn)
            else:
                tmp = Configs(fn)
                curr.merge_from(tmp)
        return curr

    def __init__(self, filename):
        with open(filename, "r") as f:
            txt = f.read()
        from . import flags as c4flags
        self.flag_aliases = c4flags.FlagAliases(yml=txt)

    def merge_from(self, other):
        self.flag_aliases = self.flag_aliases.merge_from(other.flag_aliases)
