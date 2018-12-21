# -*- coding: utf-8 -*-

"""
openxdf.signal
~~~~~~~~~~~~~~

This module allows users to read the raw signal data associated with PSG files
"""

import numpy as np
from .exceptions import XDFSourceError
from .helpers import _bytestring_to_num, _restruct_channel_epochs, timeit


class Signal(object):
    """Core Signal object.
    
    Description:
        All Signal objects wrap a single raw-signal file, and associates that
        file with its XDF header document through an OpenXDF class object.
    
    Use:
        >>> import openxdf
        >>> xdf = openxdf.OpenXDF("/path/to/file/.../example.xdf")
        >>> signals = openxdf.Signal(xdf, "/path/to/file/.../example.data")
        >>> signals.to_numeric(["FP1", "EOG"])
            {"FP1": [[100, -10, 5, -25,...], [200, -20, 10, -50, ...]],
             "EOG": [[10, -35, 25, -40,...], [65, 20, -100, -10, ...]]}
    """

    def __init__(self, xdf, filepath):
        self._xdf = xdf
        self._fpath = filepath
        self._data = self._parse()

    def __repr__(self):
        return f"<Signal [{self._xdf.id}]>"

    @property
    def _frame_information(self) -> dict:
        """Returns information about the XDF dataframe and signal channels

        Returns:
            dict: [description]
            {"FrameLength": _, "EpochLength": _, "Endian": _, "FrameWidth": _,
             "Channels": [
                 {"SourceName": _, "SampleWidth": _, "SampleFrequency": _,
                  "ChannelWidth": _, "Signed": _},
                  {...},
             ]}
        """

        frame_length = self._xdf.header["FrameLength"]

        frame_info = {}
        frame_info["FrameLength"] = frame_length
        frame_info["EpochLength"] = self._xdf.header["EpochLength"]
        frame_info["Endian"] = self._xdf.header["Endian"]
        frame_info["Num_Epochs"] = max([i["EpochNumber"] for i in self._xdf.epochs])

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

    @property
    def _read_file(self) -> bytes:
        """Returns signal file as bytestring
        
        Returns:
            bytes: Entire bytestring of signal file
        """
        with open(self._fpath, "rb") as f:
            return f.read()

    def _parse(self) -> list:
        """Returns signal-file data as a list of dictionaries.

        Returns:
            list: [{"FP1": b... , "FP2": b...},
                   {"FP1": b... , "FP2": b...},
                   ...]
        """
        signal_file = self._read_file

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

    def to_numeric(self, channels=None) -> dict:
        """Converts selection of channels from binary to a numeric vector.

        Args:
            channels (list or str, optional): Defaults to None.
                Vector of channel names to be included in final output.
                If None, all channels will be included.

        Returns:
            dict: Dictionary with each channel as keys, and a list of epochs
                as entries.
                {"FP1": [[100, -10, 5, -25,...], [200, -20, 10, -50, ...]], ...}
        """

        # Handle `channels` kwarg
        if type(channels) is str:
            channels = [channels]
        if type(channels) is list:
            pass

        signal_list = self._data
        frame_info = self._frame_information

        epochs_bytes_dict = _restruct_channel_epochs(signal_list, frame_info)
        epochs_numeric_dict = {}

        for channel in frame_info["Channels"]:
            channel_name = channel["SourceName"]
            if channels is not None and channel_name not in channels:
                continue

            sample_width = channel["SampleWidth"]
            byteorder = frame_info["Endian"]
            signed = channel["Signed"] == "true"

            epoch_array = np.array([])
            epochs_bytes = epochs_bytes_dict[channel_name]

            for epoch in epochs_bytes:
                epochs_numeric = _bytestring_to_num(
                    epoch, sample_width, byteorder, signed
                )
                if epoch_array.size:
                    try:
                        epoch_array = np.concatenate((epoch_array, epochs_numeric))
                    except ValueError:
                        pass
                else:
                    epoch_array = epochs_numeric

            epochs_numeric_dict[channel_name] = epoch_array

        return epochs_numeric_dict

    def cross_channels(self):
        numeric_epochs = self.to_numeric()
        montages = self._xdf.montages
        output = {}

        for montage in montages.keys():
            channel_1_name = montages[montage][0]["lead_1"]
            channel_2_name = montages[montage][0]["lead_2"]

            if channel_1_name is None and channel_2_name is None:
                output[montage] = []
                continue
            elif channel_1_name is None:
                output[montage] = numeric_epochs[channel_2_name]
                continue
            elif channel_2_name is None:
                output[montage] = numeric_epochs[channel_1_name]
                continue

            channel_1 = np.array([np.array(i) for i in numeric_epochs[channel_1_name]])
            channel_2 = np.array([np.array(i) for i in numeric_epochs[channel_2_name]])
            channel_diff = channel_1 - channel_2
            output[montage] = channel_diff

        del numeric_epochs
        return output

    def _edf_header(self):
        """Returns .edf header string

        See https://www.edfplus.info/specs/edf.html for header specification
        """

        def _pad(x, width):
            return str(x).ljust(width, " ")

        # Create Header dict
        num_chans = len(self._frame_information["Channels"])
        file_len = len(self._read_file)
        num_records = file_len // self._frame_information["FrameWidth"]

        header = {}
        header["version"] = _pad("0", 8)
        header["pat_id"] = _pad(self._xdf.id, 80)
        header["red_ic"] = _pad(self._xdf.id, 80)
        header["startdate"] = _pad(self._xdf.start_time.strftime("%d.%m.%y"), 8)
        header["starttime"] = _pad(self._xdf.start_time.strftime("%H.%M.%S"), 8)
        header["num_bytes"] = _pad(256 * (1 + num_chans), 8)
        header["reserved"] = _pad("", 44)
        header["num_records"] = _pad(num_records, 8)
        header["record_dur"] = _pad(self._frame_information["FrameLength"], 8)
        header["num_signals"] = _pad(num_chans, 4)

        # Channel header dict
        channel_properties = {
            "chan_name": ["SourceName", 16],
            "chan_transducer": [None, 80],
            "chan_unit": ["Unit", 8],
            "chan_physicalMin": ["PhysicalMin", 8],
            "chan_physicalMax": ["PhysicalMax", 8],
            "chan_digitalMin": ["DigitalMin", 8],
            "chan_digitalMax": ["DigitalMax", 8],
            "chan_prefilter": [None, 80],
            "chan_sampleFreq": ["SampleFrequency", 8],
            "chan_reserved": [None, 32],
        }

        header["channel_header"] = ""
        for prop in channel_properties:
            prop_key, prop_width = channel_properties[prop]

            for source in self._xdf.sources:
                prop_value = source[prop_key] if prop_key is not None else "Unknown"
                header["channel_header"] += _pad(prop_value, prop_width)

        # Build header from component dictionary
        header_str = ""
        for key in header:
            header_str += header[key]

        return header_str

    def to_edf_raw(self, opath: str):
        """Exports raw, uncrossed signals as .edf

        Args:
            opath (str): Output file path

        Example:
            >>> signals = openxdf.Signal(xdf, "/path/to/file/.../example.data")
            >>> signals.to_edf_raw("/output/path/.../example_uncrossed.edf")
        """

        edf_header = self._edf_header()

        with open(opath, "wb") as edf_file:
            edf_file.write(edf_header.encode("ASCII"))
            edf_file.write(self._read_file)
