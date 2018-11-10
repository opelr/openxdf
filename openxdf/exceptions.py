"""
openxdf.exceptions
~~~~~~~~~~~~~~~

This module contains custom exceptions.
"""


class Error(Exception):
    """Base class for exceptions in this module."""

    pass


class XDFSourceError(Error):
    """Raised when an unrecoverable error is found in the XDF source header"""

    pass
