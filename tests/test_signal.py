
from .context import openxdf
import unittest


class Signal_Test(unittest.TestCase):
    """[summary]"""

    def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self.xdf_path = "tests/data/test.xdf"
        self.signal_path = "tests/data/test.nkamp"
        self.xdf = openxdf.OpenXDF(self.xdf_path)

    def test_frame_information(self):
        frame_info = openxdf.signal._get_frame_information(self.xdf)
        assert type(frame_info) is dict

        keys = ["FrameLength", "EpochLength", "FrameWidth", "Channels"]
        assert all([i in frame_info.keys() for i in keys])

    def test_read_file(self):
        frame_info = openxdf.signal._get_frame_information(self.xdf)
        signal_list = openxdf.signal.read_file(self.signal_path, frame_info)

        assert type(signal_list) is list
        assert len(signal_list[0].keys()) == len(frame_info["Channels"])

    def test_Signal(self):
        frame_info = openxdf.signal._get_frame_information(self.xdf)
        signal_list = openxdf.signal.read_file(self.signal_path, frame_info)

        signal = openxdf.Signal(self.xdf, self.signal_path)
        assert signal._data == signal_list

    def test_restruct_channel_epochs(self):
        frame_info = openxdf.signal._get_frame_information(self.xdf)
        signal_list = openxdf.signal.read_file(self.signal_path, frame_info)

        restruct = openxdf.signal._restruct_channel_epochs(signal_list, frame_info)
        assert type(restruct) is dict
        assert "FP1" in restruct.keys()

    def test_bytestring_to_num(self):
        frame_info = openxdf.signal._get_frame_information(self.xdf)
        signal_list = openxdf.signal.read_file(self.signal_path, frame_info)
        epochs_bytes_dict = openxdf.signal._restruct_channel_epochs(signal_list, frame_info)

        channel = frame_info["Channels"][0]
        channel_name = channel["SourceName"]

        bytestring = epochs_bytes_dict[channel_name][0]
        sample_width = channel["SampleWidth"]
        byteorder = frame_info["Endian"]
        signed = channel["Signed"] == "true"

        byte_int_list = openxdf.signal._bytestring_to_num(bytestring, sample_width, byteorder, signed)
        assert type(byte_int_list) is list

        epoch_length = frame_info["EpochLength"]
        sample_freq = channel["SampleFrequency"]

        assert len(byte_int_list) == epoch_length * sample_freq

