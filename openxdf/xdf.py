"""
openxdf.xdf
~~~~~~~~~~~

This module provides the base class for reading XML data
"""

import xmltodict
import json

from .helpers import start_time, pull_header, pull_sources, pull_epochs, pull_scoring
from .helpers import pull_custom_event_list, pull_events


class OpenXDF:
    def __init__(self, filepath: str, deidentify=True):
        self._filepath = filepath
        self._data = self._parse(filepath, deidentify)

    def __repr__(self):
        return f"<OpenXDF [{self.id}]>"

    def _parse(self, fpath, deidentify):
        with open(fpath) as f:
            opened_file = f.read()
            xdf_odict = xmltodict.parse(opened_file)

        xdf = json.loads(json.dumps(xdf_odict))

        if deidentify:
            terms = ["xdf:FirstName", "xdf:LastName", "xdf:DOB", "xdf:Comments"]
            for term in terms:
                xdf["xdf:OpenXDF"]["xdf:PatientInformation"][term] = None

        return xdf["xdf:OpenXDF"]

    @property
    def id(self):
        i = self._data["xdf:PatientInformation"]["xdf:ID"]
        return str(i)

    @property
    def start_time(self):
        return start_time(self)

    @property
    def header(self):
        return pull_header(self)

    @property
    def sources(self):
        return pull_sources(self)

    @property
    def epochs(self):
        return pull_epochs(self)

    @property
    def scoring(self):
        return pull_scoring(self)

    @property
    def custom_event_list(self):
        return pull_custom_event_list(self)
    
    @property
    def events(self):
        return pull_events(self)
    
    @property
    def dataframe(self, epochs=True, events=True):
        raise NotImplementedError
        # return create_dataframe(self, epoch_information, custom_events)

    