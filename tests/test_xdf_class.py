"""[summary]
"""

from .context import openxdf
import unittest
from collections import OrderedDict


class XDF_Test(unittest.TestCase):
    """[summary]"""

    def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self.fpath = "tests/data/RBD_Scored.xdf"

    def test_read_data(self):
        xdf = openxdf.helpers.read_data(self.fpath)
        assert type(xdf) is OrderedDict
    

