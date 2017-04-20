
from .build_item import BuildItem
from collections import OrderedDict as odict


# -----------------------------------------------------------------------------
class Variant(BuildItem):
    """for variations in build flags"""

    @staticmethod
    def default_str():
        return 'none'

    @staticmethod
    def default():
        return Variant(__class__.default_str())

    @staticmethod
    def create_variants(spec_list):
        d = odict([('variants', (Variant, spec_list))])
        d = BuildItem.create(d)
        assert d.collections == ['variants']
        return d['variants']
