# -*- coding: utf-8 -*-

"""
openxdf.signal
~~~~~~~~~~~~~~

This module allows users to read the raw signal data associated with PSG files
"""

import numpy as np
from .exceptions import XDFSourceError
from .helpers import (
    _bytestring_to_num,
    timeit,
    read_channel_from_file,
    butter_bandpass,
    butter_bandpass_filter,
)


class Signal(object):
    """Core Signal object.

    Description:
        All Signal objects wrap a single raw-signal file, and associates that
        file with its XDF header document through an OpenXDF class object.

    Use:
        >>> import openxdf
        >>> xdf = openxdf.OpenXDF("/path/to/file/.../example.xdf")
        >>> signal= openxdf.Signal(xdf, "/path/to/file/.../example.data")
        >>> signal.list_channels
        ["EOG-L", "EOG-R", "F3-A2", "F4-A1", "C3-A2", "C4-A1", "O1-A2",
         "O2-A1", ...]
        >>> signal.read_file(["EOG-L", "C4-A1"])
        {'EOG-L': array([[-890, -885, -803, ...,  393,  440,  422],
                         [ 494,  396,  451, ...,  323,  338,  420],
                         [ 504,  439,  493, ...,  251,  300,  244],
                         ...,
                         [  47, -104,  -79, ...,    9, -149,  -78],
                         [  26,  -92,  -79, ...,   28, -105,  -64],
                         [  44,  -74,  -92, ...,  -38, -172,  -80]]),
         'C4-A1': array([[ 554,  504,  478, ..., -226, -259, -238],
                         [-194, -226, -231, ...,    8,   41,   68],
                         [ 134,  164,  181, ..., -128, -188, -163],
                         ...,
                         [ -29,    4,    8, ...,    3,   35,    9],
                         [ -30,   -6,    0, ...,  -26,   -5,   -8],
                         [ -39,   -8,   -8, ...,  -46,  -36,  -53]])}
    """

    def __init__(self, xdf, filepath):
        self._xdf = xdf
        self._fpath = filepath

    def __repr__(self):
        return f"<Signal [{self._xdf.id}]>"

    @property
    def _frame_information(self) -> dict:
        """Returns information about the XDF dataframe and signal channels

        Returns:
            dict: Dictionary of information about the XDF dataframe
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

        channels = {}
        total_width = 0
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
            channel["StartLocation"] = total_width
            channels[channel["SourceName"]] = channel
            total_width += channel["ChannelWidth"]

        frame_info["FrameWidth"] = sum(
            [channels[i]["ChannelWidth"] for i in channels.keys()]
        )
        frame_info["Channels"] = channels

        return frame_info

    @property
    def _source_information(self):
        """Returns information about the XDF source channels
        
        Returns:
            dict: {"PG1": {"Start": 8000, "Width": 400},
                   "A2": {"Start": 9200, "Width": 400},
                   ...,
                  }
        """
        sources = {}
        channels = self._xdf.montages.keys()
        frame_info = self._frame_information

        for channel in channels:
            lead1_name = self._xdf.montages[channel][0]["lead_1"]
            lead2_name = self._xdf.montages[channel][0]["lead_2"]

            if lead1_name is not None and lead1_name not in sources.keys():
                sources[lead1_name] = {}
                sources[lead1_name]["Start"] = frame_info["Channels"][lead1_name][
                    "StartLocation"
                ]
                sources[lead1_name]["Width"] = frame_info["Channels"][lead1_name][
                    "ChannelWidth"
                ]

            if lead2_name is not None and lead2_name not in sources.keys():
                sources[lead2_name] = {}
                sources[lead2_name]["Start"] = frame_info["Channels"][lead2_name][
                    "StartLocation"
                ]
                sources[lead2_name]["Width"] = frame_info["Channels"][lead2_name][
                    "ChannelWidth"
                ]

        return sources

    @property
    def list_channels(self):
        """List all channels defined in XDF montage
        
        Returns:
            list: ["EOG-L", "EOG-R", "F3-A2", ...]
        """
        return list(self._xdf.montages.keys())

    def read_file(self, channels=None):
        """Read interlaced channels from binary signal file

        Args:
            channels (list, optional): Defaults to None. List of channels to read.
        
        Returns:
            dict: Dictionary of np.arrays, one per channel.
        """
        if type(channels) is str:
            channels = [channels]
        if type(channels) is list:
            pass

        if channels is not None:
            if not all([i in self.list_channels for i in channels]):
                raise ValueError("All channels must be listed in 'xdf.montages'.")
        else:
            channels = self.list_channels

        channel_binary = {}
        frame_info = self._frame_information
        sources = self._source_information
        frame_width = frame_info["FrameWidth"]

        for channel in channels:
            lead1_name = self._xdf.montages[channel][0]["lead_1"]
            lead2_name = self._xdf.montages[channel][0]["lead_2"]
            
            if lead1_name is not None and lead1_name not in channel_binary.keys():
                channel_binary[lead1_name] = read_channel_from_file(
                    self._fpath,
                    start_location=sources[lead1_name]["Start"],
                    channel_width=sources[lead1_name]["Width"],
                    frame_width=frame_width,
                )
            
            if lead2_name is not None and lead2_name not in channel_binary.keys():
                channel_binary[lead2_name] = read_channel_from_file(
                    self._fpath,
                    start_location=sources[lead2_name]["Start"],
                    channel_width=sources[lead2_name]["Width"],
                    frame_width=frame_width,
                )

        # Convert to numeric
        as_numeric = {}
        for channel in channel_binary.keys():
            epochs_conversion = []
            
            sample_width = frame_info["Channels"][channel]["SampleWidth"]
            byteorder = frame_info["Endian"]
            signed = frame_info["Channels"][channel]["Signed"]
            
            for epoch in channel_binary[channel]:
                epochs_num = _bytestring_to_num(epoch, sample_width, byteorder, signed)
                epochs_conversion.append(epochs_num)
            
            as_numeric[channel] = np.vstack(epochs_conversion)

        # Cross and filter channels
        cross = {}
        for channel in channels:
            lead1_name = self._xdf.montages[channel][0]["lead_1"]
            lead2_name = self._xdf.montages[channel][0]["lead_2"]
            bp_filter = self._xdf.montages[channel][0]["filter"]
            filter_low, filter_high = list(map(float, bp_filter))

            if lead1_name is None:
                signal_data = as_numeric[lead2_name]
                sample_freq = frame_info["Channels"][lead2_name]["SampleFrequency"]
            elif lead2_name is None:
                signal_data = as_numeric[lead1_name]
                sample_freq = frame_info["Channels"][lead1_name]["SampleFrequency"]
            else:
                signal_data = as_numeric[lead1_name] - as_numeric[lead2_name]
                sample_freq = frame_info["Channels"][lead1_name]["SampleFrequency"]
            
            filtered_data = butter_bandpass_filter(signal_data, filter_low, filter_high, sample_freq)
            cross[channel] = filtered_data
        return cross

    # TODO: EDF functions should take desired channels as an argument, and
    #       should use montage channels, not raw sources.
    # def _edf_header(self):
    #     """Returns .edf header string

    #     See https://www.edfplus.info/specs/edf.html for header specification
    #     """

    #     def _pad(x, width):
    #         return str(x).ljust(width, " ")

    #     # Create Header dict
    #     num_chans = len(self._frame_information["Channels"])
    #     file_len = len(self._read_file)
    #     num_records = file_len // self._frame_information["FrameWidth"]

    #     header = {}
    #     header["version"] = _pad("0", 8)
    #     header["pat_id"] = _pad(self._xdf.id, 80)
    #     header["red_ic"] = _pad(self._xdf.id, 80)
    #     header["startdate"] = _pad(self._xdf.start_time.strftime("%d.%m.%y"), 8)
    #     header["starttime"] = _pad(self._xdf.start_time.strftime("%H.%M.%S"), 8)
    #     header["num_bytes"] = _pad(256 * (1 + num_chans), 8)
    #     header["reserved"] = _pad("", 44)
    #     header["num_records"] = _pad(num_records, 8)
    #     header["record_dur"] = _pad(self._frame_information["FrameLength"], 8)
    #     header["num_signals"] = _pad(num_chans, 4)

    #     # Channel header dict
    #     channel_properties = {
    #         "chan_name": ["SourceName", 16],
    #         "chan_transducer": [None, 80],
    #         "chan_unit": ["Unit", 8],
    #         "chan_physicalMin": ["PhysicalMin", 8],
    #         "chan_physicalMax": ["PhysicalMax", 8],
    #         "chan_digitalMin": ["DigitalMin", 8],
    #         "chan_digitalMax": ["DigitalMax", 8],
    #         "chan_prefilter": [None, 80],
    #         "chan_sampleFreq": ["SampleFrequency", 8],
    #         "chan_reserved": [None, 32],
    #     }

    #     header["channel_header"] = ""
    #     for prop in channel_properties:
    #         prop_key, prop_width = channel_properties[prop]

    #         for source in self._xdf.sources:
    #             prop_value = source[prop_key] if prop_key is not None else "Unknown"
    #             header["channel_header"] += _pad(prop_value, prop_width)

    #     # Build header from component dictionary
    #     header_str = ""
    #     for key in header:
    #         header_str += header[key]

    #     return header_str

    # def to_edf_raw(self, opath: str):
    #     """Exports raw, uncrossed signals as .edf

    #     Args:
    #         opath (str): Output file path

    #     Example:
    #         >>> signals = openxdf.Signal(xdf, "/path/to/file/.../example.data")
    #         >>> signals.to_edf_raw("/output/path/.../example_uncrossed.edf")
    #     """

    #     edf_header = self._edf_header()

    #     with open(opath, "wb") as edf_file:
    #         edf_file.write(edf_header.encode("ASCII"))
    #         edf_file.write(self._read_file)
