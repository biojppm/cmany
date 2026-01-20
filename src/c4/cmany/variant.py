
from .build_item import BuildItem
from collections import OrderedDict as odict


# -----------------------------------------------------------------------------
class Variant(BuildItem):
    """for variations in build flags"""

    @staticmethod
    def default_str(toolchain_file: str=None):
        return 'none'

    @staticmethod
    def default(toolchain_file: str=None):
        return Variant(__class__.default_str())

    @staticmethod
    def create_variants(spec_list):
        name_and_class = odict([('variants', Variant)])
        d = BuildItem.create_build_items(name_and_class, variants=spec_list)
        assert d.collections == ['variants']
        return d['variants']
