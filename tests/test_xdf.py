# -*- coding: utf-8 -*-

from .context import openxdf
import unittest
from datetime import datetime
import pandas as pd


class XDF_Test(unittest.TestCase):
    """Test cases for the openxdf.xdf module"""

    def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self.xdf_path = "tests/data/test.xdf"
        self.xdf = openxdf.OpenXDF(self.xdf_path)

    def test_read_data(self):
        assert type(self.xdf) is openxdf.xdf.OpenXDF
        assert type(self.xdf._data) is dict

    def test_id(self):
        xdf_id = self.xdf.id
        assert type(xdf_id) is str

    def test_start_time(self):
        start_time = self.xdf.start_time
        assert type(start_time) is datetime

    def test_headers(self):
        header = self.xdf.header
        assert type(header) is dict

        keys = ["ID", "EpochLength", "FrameLength", "Endian", "File"]
        assert all([i in header.keys() for i in keys])

    def test_sources(self):
        source = self.xdf.sources
        assert type(source) is list
        assert type(source[0]) is dict
    
    def test_montages(self):
        montage = self.xdf.montages
        assert type(montage) is dict
        assert montage != {}

    def test_scoring(self):
        scoring = self.xdf.scoring
        assert type(scoring) is list
        assert len(scoring) >= 1

    def test_dataframe(self):
        df = self.xdf.dataframe()
        assert type(df) is pd.DataFrame
        assert not df.empty
