#!/usr/bin/env python3

import os.path
import sys
from collections import OrderedDict as odict

topics = odict()


class Topic:

    keylen = 0
    tablefmt = None

    def __init__(self, id, title, txt, disabled=False):
        self.id = id
        self.title = title
        self.__doc__ = title
        self.txt = txt
        Topic.keylen = max(Topic.keylen, len(id))
        Topic.tablefmt = '    {:' + str(Topic.keylen) + '} {}'
        if not disabled:
            topics[id] = self


def create_topic(id, title, txt, disabled=False):
    ht = Topic(id, title, txt, disabled)
    setattr(sys.modules[__name__], 'help_' + id, ht)


def _get_doc(topic_name):
    txtdocs = os.path.abspath(os.path.dirname(__file__) +
                              "/../../../doc/_build/text")
    with open(os.path.join(txtdocs, topic_name + ".txt")) as f:
        txt = "".join(f.readlines())
    return txt


# -----------------------------------------------------------------------------
create_topic(
    "examples",
    title="Basic usage examples",
    txt=_get_doc("basic_usage")
)


# -----------------------------------------------------------------------------
create_topic(
    "variants",
    title="Specifying build variants",
    txt=_get_doc("variants")
)


# -----------------------------------------------------------------------------
create_topic(
    "flags",
    title="Specifying compiler flags",
    txt=_get_doc("flags")
)


# -----------------------------------------------------------------------------
create_topic(
    "vs",
    title="Specifying Microsoft Visual Studio versions and toolsets",
    txt=_get_doc("vs")
)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
epilog = """

list of help topics:
""" + '\n'.join([Topic.tablefmt.format(k, v.title) for k, v in topics.items()])
