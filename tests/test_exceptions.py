from .context import openxdf
import unittest


class Signal_Test(unittest.TestCase):
    """[summary]"""

    def __init__(self, methodName="runTest"):
        super().__init__(methodName)

    def test_exception(self):
        def broken():
            raise openxdf.exceptions.XDFSourceError("Bad")
        
        with self.assertRaises(openxdf.exceptions.XDFSourceError) as e:
            broken()
        
