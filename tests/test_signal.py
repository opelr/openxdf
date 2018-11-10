
from .context import openxdf
import unittest


class Signal_Test(unittest.TestCase):
    """[summary]"""

    def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self.xdf_path = "tests/data/test.xdf"
        self.signal_path = "tests/data/test.nkamp"
        self.xdf = openxdf.OpenXDF(self.xdf_path)

    def test_Signal(self):
        signal = openxdf.Signal(self.xdf, self.signal_path)
        assert type(signal) == openxdf.Signal
    
    def test_frame_information(self):
        signal = openxdf.Signal(self.xdf, self.signal_path)
        frame_info = signal._frame_information
        assert type(frame_info) is dict

        keys = ["FrameLength", "EpochLength", "FrameWidth", "Channels"]
        assert all([i in frame_info.keys() for i in keys])

    def test_parse(self):
        signal = openxdf.Signal(self.xdf, self.signal_path)
        signal_list = signal._parse()
        frame_info = signal._frame_information

        assert type(signal_list) is list
        assert len(signal_list[0].keys()) == len(frame_info["Channels"])

    # def test_to_numeric(self):
    #     frame_info = openxdf.signal._get_frame_information(self.xdf)
    #     signal_list = openxdf.signal.read_file(self.signal_path, frame_info)

    #     numeric = openxdf.signal._to_numeric(signal_list, frame_info)
    #     assert type(numeric) is dict
    #     assert "FP1" in numeric.keys()
