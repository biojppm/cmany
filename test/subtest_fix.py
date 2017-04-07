import unittest as ut
import types
import sys

# TestCase.subTest() was introduced only in Python 3.4,
# so we provide a replacement implementation to use in older Python versions.


def mysubTestFunc(self, msg=None, **params):
    return mysubTest(self, msg, **params)


if sys.version_info < (3, 4):
    # http://stackoverflow.com/questions/6118592/dynamically-add-member-function-to-an-instance-of-a-class-in-python
    ut.TestCase.subTest = types.MethodType(mysubTestFunc, ut.TestCase)


# -----------------------------------------------------------------------------
class mysubTest:
    """this is a quick and dirty implementation"""

    def __init__(self, obj, msg=None, **params):
        self.obj = obj
        self.msg = msg
        self.params = params

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        pass
