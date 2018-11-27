# -*- coding: utf-8 -*-

from .context import openxdf
import unittest


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

    def test_parse(self):
        signal_list = self.signal._parse()
        frame_info = self.signal._frame_information

        assert type(signal_list) is list
        assert len(signal_list[0].keys()) == len(frame_info["Channels"])

    def test_to_numeric(self):
        numeric = self.signal.to_numeric(channels="FP1")

        assert type(numeric) is dict
        assert "FP1" in numeric.keys()

        total_epochs = self.signal._frame_information["Num_Epochs"]
        assert len(numeric["FP1"]) == total_epochs

    def test_edf_header(self):
        edf_header = self.signal._edf_header()
        assert type(edf_header) is str

        num_channels = len(self.signal._xdf.sources)
        init_len = 256
        chan_len = 256
        total_len = init_len + (num_channels * chan_len)
        assert len(edf_header) == total_len

        with open("tests/data/edf_header.edf", "wb") as f:
            f.write(edf_header.encode("ascii"))

    def test_to_edf(self):
        self.signal.to_edf("tests/data/test.edf")
