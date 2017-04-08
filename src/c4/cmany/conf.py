import os.path as osp

CONF_DIR = osp.join(osp.dirname(__file__), "conf")
if not osp.exists(CONF_DIR):
    CONF_DIR = osp.abspath(osp.join(osp.dirname(__file__), "../../../conf"))
    assert osp.exists(CONF_DIR)

USER_DIR = osp.expanduser("~/.cmany/")

CONF_FLAGS_FILE = osp.join(CONF_DIR, 'flags.yml')
USER_FLAGS_FILE = osp.join(USER_DIR, 'flags.yml')
