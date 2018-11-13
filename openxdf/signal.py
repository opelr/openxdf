"""
openxdf.signal
~~~~~~~~~~~~~~~

This module allows users to read the raw signal data associated with PSG files
"""

from .exceptions import XDFSourceError
from .helpers import _bytestring_to_num, _restruct_channel_epochs


class Signal:
    def __init__(self, xdf, filepath):
        self._xdf = xdf
        self._fpath = filepath
        self._data = self._parse()

    def __repr__(self):
        return f"<Signal [{self._xdf.id}]>"

    @property
    def _frame_information(self):
        """[summary]
        
        Returns:
            dict: [description]
        """

        frame_length = self._xdf.header["FrameLength"]

        frame_info = {}
        frame_info["FrameLength"] = frame_length
        frame_info["EpochLength"] = self._xdf.header["EpochLength"]
        frame_info["Endian"] = self._xdf.header["Endian"]

        channels = []

        for source in self._xdf.sources:
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

    def _parse(self):
        """[summary]
        
        Returns:
            list: [{"FP1": b... , "FP2": b...},
                   {"FP1": b... , "FP2": b...},
                   ...]
        """
        with open(self._fpath, "rb") as f:
            signal_file = f.read()

        file_list = []
        frame_info = self._frame_information
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

    def to_numeric(self):
        raise NotImplementedError

    def to_edf(self):
        raise NotImplementedError


def _to_numeric(signal_list: list, frame_info: dict):
    epochs_bytes_dict = _restruct_channel_epochs(signal_list, frame_info)
    epochs_numeric_dict = {}

    for channel in frame_info["Channels"]:
        channel_name = channel["SourceName"]
        sample_width = channel["SampleWidth"]
        byteorder = frame_info["Endian"]
        signed = channel["Signed"] == "true"

        epochs_numeric_list = []
        epochs_bytes = epochs_bytes_dict[channel_name]

        for epoch in epochs_bytes:
            epochs_numeric = _bytestring_to_num(epoch, sample_width, byteorder, signed)
            epochs_numeric_list.append(epochs_numeric)

        epochs_numeric_dict[channel_name] = epochs_numeric_list

    return epochs_numeric_dict


def to_edf():
    raise NotImplementedError
