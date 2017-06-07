#!/usr/bin/env python3

import os.path as osp
import sys
from collections import OrderedDict as odict

from c4.cmany import conf

topics = odict()


class Topic:

    keylen = 0
    tablefmt = None

    def __init__(self, id, title, txt, disabled=False):
        self.id = id
        self.title = title
        self.__doc__ = title
        self.txt = txt
        Topic.keylen = max(Topic.keylen, len(id)) + 1
        Topic.tablefmt = '    {:' + str(Topic.keylen) + '} {}'
        if not disabled:
            topics[id] = self


def create_topic(id, title, txt, disabled=False):
    ht = Topic(id, title, txt, disabled)
    setattr(sys.modules[__name__], 'help_' + id, ht)


def _get_doc(topic_name):
    with open(osp.join(conf.DOC_DIR, topic_name + ".txt")) as f:
        txt = "".join(f.readlines())
    return txt


# -----------------------------------------------------------------------------
create_topic(
    "quick_tour",
    title="Quick tour",
    txt=_get_doc("quick_tour")
)


# -----------------------------------------------------------------------------
create_topic(
    "build_items",
    title="Specifying build items",
    txt=_get_doc("build_items")
)


# -----------------------------------------------------------------------------
create_topic(
    "flags",
    title="Specifying compiler flags and build-item specific properties",
    txt=_get_doc("flags")
)


# -----------------------------------------------------------------------------
create_topic(
    "vs",
    title="Specifying Microsoft Visual Studio versions and toolsets",
    txt=_get_doc("vs")
)


# -----------------------------------------------------------------------------
create_topic(
    "dependencies",
    title="Dealing with project dependencies",
    txt=_get_doc("dependencies")
)


# -----------------------------------------------------------------------------
create_topic(
    "reusing_arguments",
    title="Simplify the input to cmany.",
    txt=_get_doc("reusing_arguments")
)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
epilog = """

list of help topics:
{}
""".format(
    '\n'.join([Topic.tablefmt.format(k, v.title) for k, v in topics.items()])
)
