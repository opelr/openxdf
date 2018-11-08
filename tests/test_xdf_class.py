
from .context import openxdf
import unittest


class XDF_Test(unittest.TestCase):
    """[summary]"""

    def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self.fpath = "tests/data/test.xdf"
        self.xdf = openxdf.OpenXDF(self.fpath)

    def test_read_data(self):
        assert type(self.xdf) is openxdf.xdf.OpenXDF
        assert type(self.xdf._data) is dict

    def test_id(self):
        xdf_id = self.xdf.id
        assert type(xdf_id) is str

    def test_start_time(self):
        start_time = self.xdf.start_time
        # print(start_time)

    def test_headers(self):
        header = self.xdf.header
        assert type(header) is dict

        keys = ["id", "epoch_length", "frame_length", "endian", "file"]
        assert all([i in header.keys() for i in keys])

    def test_sources(self):
        source = self.xdf.sources
        assert type(source) is list
        assert type(source[0]) is dict

    def test_scoring(self):
        scoring = self.xdf.scoring