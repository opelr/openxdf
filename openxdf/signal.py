"""
openxdf.signal
~~~~~~~~~~~~~~~

This module allows users to read the raw signal data associated with PSG files
"""

# import openxdf
# xdf = openxdf.OpenXDF("tests/data/test.xdf")
# fpath = "tests/data/test.nkamp"

from .exceptions import XDFSourceError


class Signal:
    def __init__(self, xdf, filepath):
        self._xdf = xdf
        self._fpath = filepath
        self._data = self._parse()

    def __repr__(self):
        return f"<Signal [{self._xdf.id}]>"

    @property
    def _frame_information(self):
        return _get_frame_information(self._xdf)

    def _parse(self):
        return read_file(self._fpath, self._frame_information)

    def to_numeric(self):
        raise NotImplementedError

    def to_edf(self):
        raise NotImplementedError


def _get_frame_information(xdf) -> dict:
    """[summary]
    
    Args:
        xdf (openxdf.OpenXDF): [description]
    
    Returns:
        dict: [description]
    """

    frame_length = xdf.header["FrameLength"]
    epoch_length = xdf.header["EpochLength"]

    frame_info = {}
    frame_info["FrameLength"] = frame_length
    frame_info["EpochLength"] = epoch_length

    channels = []

    for source in xdf.sources:
        channel = {}
        channel["SourceName"] = source["SourceName"]
        sample_width = source["SampleWidth"]
        sample_freq = source["SampleFrequency"]

        if sample_freq == 0:
            raise XDFSourceError("Source sample frequency has 0 value.")
        if sample_width == 0:
            raise XDFSourceError("Source sample width has 0 value.")

        channel["SampleWidth"] = sample_width
        channel["SampleFrequency"] = sample_freq
        channel["ChannelWidth"] = sample_width * sample_freq * frame_length
        channel["Signed"] = source["Signed"]
        channels.append(channel)

    frame_info["FrameWidth"] = sum([i["ChannelWidth"] for i in channels])
    frame_info["Channels"] = channels

    return frame_info


def read_file(fpath: str, frame_info) -> list:
    """[summary]
    
    Args:
        fpath (str): [description]
        frame_information ([type]): [description]
    
    Returns:
        list: [{"FP1": b... , "FP2": b...},
               {"FP1": b... , "FP2": b...},
               ...]
    """
    with open(fpath, "rb") as f:
        signal_file = f.read()

    file_list = []
    frames = len(signal_file) / frame_info["FrameWidth"]
    for frame_num in range(int(frames)):
        frame_dict = {}

        bit_shift = frame_num * frame_info["FrameWidth"]
        start_bit = 0
        for channel in frame_info["Channels"]:
            channel_name = channel["SourceName"]
            channel_width = channel["ChannelWidth"]

            byte_from = bit_shift + start_bit
            byte_to = byte_from + channel_width

            frame_dict[channel_name] = signal_file[byte_from:byte_to]

            start_bit = start_bit + channel_width

        file_list.append(frame_dict)

    return file_list


def _restruct_channel_epochs(signal_list: list, frame_info: dict):
    """[summary]
    
    Args:
        signal_list (list): [description]
        frame_info (dict): [description]
    """
    epoch_length = frame_info["EpochLength"]
    num_epochs = len(signal_list)
    channels_epochs_bytes = {}

    for channel in frame_info["Channels"]:
        sample_width = channel["SampleWidth"]
        channel_name = channel["SourceName"]

        epochs = []

        for start_frame in range(0, num_epochs, epoch_length):
            bytestring = b""

            for frame in signal_list[start_frame : start_frame + epoch_length]:
                bytestring += frame[channel_name]

            epochs.append(bytestring)

        channels_epochs_bytes[channel_name] = epochs

    return channels_epochs_bytes


def to_numeric(signal_list: list, frame_info: dict):
    # epochs_bytes: dict = _restruct_channel_epochs(signal_list, frame_info)

    # for channel in frame_info["Channels"]:
    #     signed = channel["Signed"] == "true"
    
    raise NotImplementedError


def to_edf():
    raise NotImplementedError
