"""
OpenXDF Module
~~~~~~~~~~~~~~

OpenXDF is a Python module built for interacting with Open eXchange Data Format
files. Basic usage: 

   >>> import openxdf
   >>> xdf = openxdf.OpenXDF("/path/to/file/.../example.xdf")
   >>> xdf.header
   {"ID": "Example", "EpochLength": 30, "FrameLength": 1, "Endian": "little",
    "File": "Example.rawdata"}
   >>> xdf.sources
   [{"SourceName": "FP1", "Unit": 1e-06, "UseGridScale": "false",
     "MinSamplingRate": 200, "MinSampleWidth": 1, "Ignore": "false",
     "PhysicalMax": 3199.9, "Signed": "true", "SampleWidth": 2,
     "SampleFrequency": 200, "DigitalMax": 32767, "DigitalMin": -32768,
     "PhysicalMin": -3200, "DigitalToVolts": 0.0976563},
     {...},
    ]

   >>> signals = openxdf.Signal(xdf, "/path/to/file/.../example.data")
   >>> signals.to_numeric(["FP1", "EOG"])
   {"FP1": [[100, -10, 5, -25,...], [200, -20, 10, -50, ...]],
    "EOG": [[10, -35, 25, -40,...], [65, 20, -100, -10, ...]]}
   >>> signals.to_edf("/output/path/.../example.edf")
"""

from .__version__ import __title__, __description__, __url__, __version__
from .__version__ import __author__, __author_email__, __license__
from .__version__ import __copyright__


from openxdf.xdf import OpenXDF
from openxdf.signal import Signal


__all__ = ["OpenXDF", "Signal"]
