# -*- coding: utf-8 -*-

from .context import openxdf
import unittest
import numpy as np


class Signal_Test(unittest.TestCase):
    """Test cases for the openxdf.signal module"""

    def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self.xdf_path = "tests/data/test.xdf"
        self.signal_path = "tests/data/test.nkamp"
        self.xdf = openxdf.OpenXDF(self.xdf_path)
        self.signal = openxdf.Signal(self.xdf, self.signal_path)

    def test_Signal(self):
        assert type(self.signal) == openxdf.Signal

    def test_frame_information(self):
        frame_info = self.signal._frame_information
        assert type(frame_info) is dict

        keys = [
            "FrameLength",
            "EpochLength",
            "FrameWidth",
            "Endian",
            "Num_Epochs",
            "Channels",
        ]
        assert all([i in frame_info.keys() for i in keys])
    
    def test_source_information(self):
        source_info = self.signal._source_information
        assert type(source_info) is dict

        all_sources = [i["SourceName"] for i in self.signal._xdf.sources]
        assert all(i in all_sources for i in source_info.keys())

    def test_read_file(self):
        channel = self.signal.list_channels[0]
        output = self.signal.read_file(channels=channel)
        
        assert type(output) is dict
        assert channel in output.keys()
        assert type(output[channel]) is np.ndarray
        assert output[channel].size

    # def test_edf_header(self):
    #     edf_header = self.signal._edf_header()
    #     assert type(edf_header) is str

    #     num_channels = len(self.signal._xdf.sources)
    #     init_len = 256
    #     chan_len = 256
    #     total_len = init_len + (num_channels * chan_len)
    #     assert len(edf_header) == total_len

    #     with open("tests/data/edf_header.edf", "wb") as f:
    #         f.write(edf_header.encode("ascii"))

    # def test_to_edf_raw(self):
    #     self.signal.to_edf_raw("tests/data/test.edf")
