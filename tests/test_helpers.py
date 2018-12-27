# -*- coding: utf-8 -*-

from .context import openxdf
import numpy as np
import unittest


class Helpers_Test(unittest.TestCase):
    """Test cases for the openxdf.helpers module"""

    def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self.xdf_path = "tests/data/test.xdf"
        self.signal_path = "tests/data/test.nkamp"
        self.xdf = openxdf.OpenXDF(self.xdf_path)
        self.signal = openxdf.Signal(self.xdf, self.signal_path)

    # def test_bytestring_to_num(self):
    #     frame_info = self.signal._frame_information
    #     signal_list = self.signal._data
    #     epochs_bytes_dict = openxdf.helpers._restruct_channel_epochs(
    #         signal_list, frame_info
    #     )

    #     channel = frame_info["Channels"][0]

    #     bytestring = epochs_bytes_dict[channel["SourceName"]][0]
    #     sample_width = channel["SampleWidth"]
    #     byteorder = frame_info["Endian"]
    #     signed = channel["Signed"] == "true"

    #     byte_int_list = openxdf.helpers._bytestring_to_num(
    #         bytestring, sample_width, byteorder, signed
    #     )
    #     assert type(byte_int_list) is np.ndarray

    #     epoch_length = frame_info["EpochLength"]
    #     sample_freq = channel["SampleFrequency"]

    #     assert len(byte_int_list[0]) == epoch_length * sample_freq

    def test_clean_title(self):
        assert openxdf.helpers.clean_title("xdf:Test") == "Test"
        assert openxdf.helpers.clean_title("nti:Test") == "Test"
