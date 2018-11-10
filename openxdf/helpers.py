"""
openxdf.helpers
~~~~~~~~~~~~~~~

Helper functions
"""

from datetime import datetime
import re
import pandas as pd


def clean_title(title: str) -> str:
    """Remove 'nti:' and 'xdf:' motifs from a str
    
    Args:
        title (str): Single string with motif
    
    Returns:
        str: Cleaned string
    """
    return re.sub("nti:|xdf:", "", title)


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


def _bytestring_to_num(bytestring, sample_width, byteorder, signed):
    conversion = []
    for idx in range(0, len(bytestring), sample_width):
        idx_bytes = bytestring[idx : idx + sample_width]
        i = int.from_bytes(idx_bytes, byteorder=byteorder, signed=signed)
        conversion.append(i)

    return conversion
