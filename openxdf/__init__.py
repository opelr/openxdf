"""
OpenXDF Module
~~~~~~~~~~~~~~

openxdf is a library for reading (OpenXDF)[http://openxdf.org/] formatted
files. Basic usage: 

   >>> import openxdf
   >>> xdf = openxdf.OpenXDF("/path/to/file/.../example.xdf")
   >>> xdf.
"""

from .__version__ import __title__, __description__, __url__, __version__
from .__version__ import __author__, __author_email__, __license__
from .__version__ import __copyright__


from .xdf import OpenXDF


__all__ = ["OpenXDF"]
