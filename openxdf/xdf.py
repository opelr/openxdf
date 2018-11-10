"""
openxdf.xdf
~~~~~~~~~~~

This module provides the base class for reading XML data
"""

import xmltodict
import json
from datetime import datetime
import re

from .helpers import clean_title

# from .helpers import start_time, pull_header, pull_sources, pull_epochs, pull_scoring
# from .helpers import pull_custom_event_list, pull_events


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
        data_file = self._data["xdf:DataFiles"]["xdf:DataFile"]

        if type(data_file) is dict:
            session = data_file["xdf:Sessions"]["xdf:Session"]
        elif type(data_file) is list:
            session = data_file[0]["xdf:Sessions"]["xdf:Session"]
        else:
            raise TypeError

        return datetime.strptime(session["xdf:StartTime"][:-9], "%Y-%m-%dT%H:%M:%S.%f")

    @property
    def header(self):
        header = {}
        data_file = self._data["xdf:DataFiles"]["xdf:DataFile"]

        header["ID"] = re.sub("[.]nkamp", "", data_file["xdf:File"])
        header["EpochLength"] = int(self._data["xdf:EpochLength"])
        header["FrameLength"] = int(data_file["xdf:FrameLength"])
        header["Endian"] = data_file["xdf:Endian"]
        header["File"] = data_file["xdf:File"]

        return header

    @property
    def sources(self):
        sources = self._data["xdf:DataFiles"]["xdf:DataFile"]["xdf:Sources"]["xdf:Source"]

        for source in sources:
            for k, v in source.items():
                new_key = clean_title(k)
                source[new_key] = source.pop(k)

                if re.match("[0-9]+[\.e][-]?[0-9]+", str(v)) is not None:
                    source[new_key] = float(str(v))
                elif re.match("[0-9]+", str(v)) is not None:
                    source[new_key] = int(str(v))

        return sources

    @property
    def epochs(self):
        """Extract epoch information from raw data

        Returns:
            dict: Dict with epoch information
        """
        if "xdf:ScoringResults" not in self._data.keys():
            return {}

        epochs = self._data["xdf:ScoringResults"]["xdf:EpochInformation"]["xdf:Epoch"]
        for epoch in epochs:
            for k, v in epoch.items():
                new_key = clean_title(k)
                epoch[new_key] = epoch.pop(k)

                if re.match("[0-9]+[\.|e][-]?[0-9]+", str(v)) is not None:
                    epoch[new_key] = float(v)
                elif re.match("[0-9]+", str(v)) is not None:
                    epoch[new_key] = int(v)

        return epochs

    @property
    def scoring(self):
        if "xdf:ScoringResults" not in self._data.keys():
            return {}

        scoring_info = []

        scorers = self._data["xdf:ScoringResults"]["xdf:Scorers"]["xdf:Scorer"]
        for scorer in scorers:
            header = {}
            header["first_name"] = scorer["xdf:FirstName"]
            header["last_name"] = scorer["xdf:LastName"]

            staging = {}
            for epoch in scorer["xdf:SleepStages"]["xdf:SleepStage"]:
                staging[epoch["xdf:EpochNumber"]] = epoch["xdf:Stage"]

            scoring_info.append({"header": header, "staging": staging})

        return scoring_info

    @property
    def custom_event_list(self):
        custom_events = {}

        scorers = self._data["xdf:ScoringResults"]["xdf:Scorers"]["xdf:Scorer"]
        for scorer in scorers:
            ce_configs = scorer["nti:CEConfigs"]
            if ce_configs is None:
                continue
            for config in ce_configs["nti:CEConfig"]:
                ce_type = config["nti:CEType"]
                custom_events[ce_type] = {}
                custom_events[ce_type]["name"] = config["nti:CEName"]
                custom_events[ce_type]["default_dur"] = int(config["nti:CEDefaultDur"])
                custom_events[ce_type]["min_dur"] = int(config["nti:CEMinDur"])
                custom_events[ce_type]["max_dur"] = int(config["nti:CEMaxDur"])

        return custom_events
    
    @property
    def events(self):
        events = {}
        section_headers = [
            "xdf:Apneas",
            "xdf:Hypopneas",
            "xdf:Desaturations",
            "xdf:Microarousals",
            "xdf:Snores",
            "xdf:LegMovements1",
            "xdf:LegMovements2",
            "nti:CustomEvents",
        ]
        sections = [[i, re.sub("s[0-9]?$", "", i)] for i in section_headers]

        scorers = self._data["xdf:ScoringResults"]["xdf:Scorers"]["xdf:Scorer"]
        for scorer in scorers:
            s_name = scorer["xdf:FirstName"]
            events[s_name] = {}
            for head, body in sections:
                h_name = clean_title(head)

                clean_body = []

                if scorer[head] is None:
                    continue

                for e in scorer[head][body]:
                    clean_e = {clean_title(k): v for k, v in e.items()}
                    clean_body.append(clean_e)

                events[s_name][h_name] = clean_body

        return events
    
    @property
    def dataframe(self, epochs=True, events=True):
        # if epochs:
        #     epoch_df = pd.DataFrame(xdf.epochs)
        # TODO: Unpack openxdf.events and openxdf.scoring dicts into dataframes
        raise NotImplementedError
    