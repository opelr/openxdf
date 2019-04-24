# -*- coding: utf-8 -*-

"""
openxdf.helpers
~~~~~~~~~~~~~~~

Helper functions
"""

import os
import re
from struct import iter_unpack
from itertools import chain
import numpy as np
from scipy.signal import butter, lfilter
from time import time


def clean_title(title: str) -> str:
    """Remove 'nti:' and 'xdf:' motifs from a str

    Args:
        title (str): Single string with motif

    Returns:
        str: Cleaned string
    """
    return re.sub("nti:|xdf:", "", title)


def _bytestring_to_num(bytestring, sample_width, byteorder, signed) -> list:
    """Converts bytestring to a list of numeric values.

    Args:
        bytestring (bytes): Bytes object to be converted.
        sample_width (int): Sample size in bytes.
        byteorder (str): Endian-ness for multibyte samples.
        signed (bool): True indicates a signed sample (e.g. can be +/-).

    Returns:
        list: Bytestring converted to numeric values.
    """

    fmt = "@"
    if byteorder.lower() == "little":
        fmt = "<"
    elif byteorder.lower() == "big":
        fmt = ">"

    ctype = {"1": "b", "2": "h", "4": "l", "8": "q"}
    c = ctype[str(sample_width)]

    if signed:
        fmtc = fmt + c
    else:
        fmtc = fmt + c.upper()

    conversion = iter_unpack(fmtc, bytestring)
    return np.array([list(chain(*conversion))])


def timeit(method):
    """Deorator function to help with timing
    
    Args:
        method (function): Function to time
    """

    def timed(*args, **kw):
        ts = time()
        result = method(*args, **kw)
        te = time()
        print("%r  %2.2f ms" % (method.__name__, (te - ts) * 1000))
        return result

    return timed


def read_channel_from_file(fpath, start_location, channel_width, frame_width, frame_length = 1, start = 0, end = 1e9):
    """Returns channel information from interleaved binary file
    
    Args:
        fpath (str): Filepath.
        start_location (int): Number of bytes from start of window.
        channel_width (int): Number of bytes the channel takes.
        frame_width (int): Width of all channels in a single period.
        frame_length (int): Length of each frame in seconds.
        start (int): Start of recording to be returned in seconds.
        end (int): End of recording to be returned in seconds.
    
    Returns:
        list: List containing one bytestring per period for the channel.
    """
    end_time = int(os.path.getsize(fpath)/frame_width) - 1
    if end > end_time:
        end = end_time
    
    if start % frame_length != 0:
        start = start - (start % frame_length)
    
    if end % frame_length != 0:
        end = end - (end % frame_length)
    
    assert start < end, 'Start time must be less than end time!'
    
    output = []
    f = open(fpath, "rb")

    for i in range(start,end+1):
        f.seek(i*frame_width + start_location, 0)
        output.append(f.read(channel_width))
        start += frame_width
    f.close()
    return output


def butter_bandpass(lowcut, highcut, fs, order=5):
    """[summary]
    
    Args:
        lowcut ([type]): [description]
        highcut ([type]): [description]
        fs ([type]): [description]
        order (int, optional): Defaults to 5. [description]
    
    Returns:
        [type]: [description]
    """
    def _switch(x):
        if x == 0:
            return 0.00001
        elif x == 1:
            return 0.99999
        else:
            return x
    
    nyq = 0.5 * fs
    low = _switch(lowcut / nyq)
    high = _switch(highcut / nyq)
    b, a = butter(order, [low, high], btype="band")
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    """[summary]
    
    Args:
        data ([type]): [description]
        lowcut ([type]): [description]
        highcut ([type]): [description]
        fs ([type]): [description]
        order (int, optional): Defaults to 5. [description]
    
    Returns:
        [type]: [description]
    """
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y
