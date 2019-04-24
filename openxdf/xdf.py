# -*- coding: utf-8 -*-

"""
openxdf.xdf
~~~~~~~~~~~

This module provides the base class for reading XML data
"""

import xmltodict
import json
from datetime import datetime
import re
import pandas as pd
from math import ceil

from .helpers import clean_title

class OpenXDF(object):
    """Core OpenXDF object. Wraps a single XDF header document.
    """

    def __init__(self, filepath: str, deidentify=True):
        self._filepath = filepath
        self._data = self._parse(filepath, deidentify)

    def __repr__(self):
        return f"<OpenXDF [{self.id}]>"

    def _parse(self, fpath, deidentify) -> dict:
        """Reads OpenXDF file and converts XML structure to a dict.

        Args:
            fpath (str): Filepath
            deidentify (bool): Should potentially sensitive information be
                removed upon reading the file?

        Returns:
            dict: XDF file as a dict object.
        """
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
        """Returns general file encoding information.
        """

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
        """Information on raw data sources (e.g. signals)"""
        sources = self._data["xdf:DataFiles"]["xdf:DataFile"]["xdf:Sources"][
            "xdf:Source"
        ]

        for source in sources:
            for k, v in source.items():
                new_key = clean_title(k)
                source[new_key] = source.pop(k)

                if re.match("[-]?[0-9]+[\.e][-]?[0-9]+", str(v)) is not None:
                    source[new_key] = float(str(v))
                elif re.match("[-]?[0-9]+", str(v)) is not None:
                    source[new_key] = int(str(v))

        return sources

    @property
    def montages(self):
        """Information on montages"""
        montages = self._data["xdf:DataFiles"]["xdf:DataFile"]["xdf:Montages"][
            "xdf:Montage"
        ]

        crosses = {}

        for montage in montages:
            channels = montage["xdf:Channels"]["xdf:Channel"]
            for channel in channels:
                label = channel["xdf:Label"]
                lead_1 = channel["xdf:G1"]
                lead_2 = channel["xdf:G2"]
                filter_low = channel["xdf:LF"]
                filter_high = channel["xdf:HF"]

                channel_info = {
                    "lead_1": lead_1,
                    "lead_2": lead_2,
                    "filter": [filter_low, filter_high],
                }

                if label in crosses.keys():
                    if not channel_info in crosses[label]:
                        crosses[label].append(channel_info)
                else:
                    crosses[label] = [channel_info]

        return crosses

    @property
    def epochs(self):
        """Extracts epoch information

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
        """Extracts sleep scoring information"""

        if "xdf:ScoringResults" not in self._data.keys():
            return {}

        scoring_info = []

        scorers = self._data["xdf:ScoringResults"]["xdf:Scorers"]["xdf:Scorer"]
        for scorer in scorers:
            header = {}
            header["first_name"] = scorer["xdf:FirstName"]
            header["last_name"] = scorer["xdf:LastName"]

            staging = []
            if (
                scorer["xdf:SleepStages"] is None
                or scorer["xdf:SleepStages"]["xdf:SleepStage"] is None
            ):
                continue

            for epoch in scorer["xdf:SleepStages"]["xdf:SleepStage"]:
                e = {}
                e["EpochNumber"] = int(epoch["xdf:EpochNumber"])
                e["Stage"] = epoch["xdf:Stage"]
                staging.append(e)

            scoring_info.append({"header": header, "staging": staging})

        return scoring_info

    @property
    def custom_event_list(self):
        """Returns a dict of the custom events defined across scorers"""

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
        """Returns a dict of all events across all scorers, incl. custom events
        """

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
                    if e is None or type(e) is not dict:
                        continue

                    clean_e = {clean_title(k): v for k, v in e.items()}
                    clean_body.append(clean_e)

                events[s_name][h_name] = clean_body

        return events

    def dataframe(self, epochs=True, events=True) -> pd.DataFrame:
        """Returns DataFrame of scoring, epoch, and event information.

        Arguments:
            epochs (bool, optional): Defaults to True. Include epoch info?
            events (bool, optional): Defaults to True. Include event info?

        Returns:
            pd.DataFrame: DataFrame of scoring, epochs, and events.
        """

        # Scoring
        scoring_df = pd.DataFrame()
        for scorer in self.scoring:
            _staging_df = pd.DataFrame(scorer["staging"])
            _staging_df["Scorer"] = scorer["header"]["first_name"]
            scoring_df = scoring_df.append(_staging_df)

        scoring_df = scoring_df.sort_values(["EpochNumber", "Scorer"])
        scoring_df = scoring_df.reset_index(drop=True)

        # Epochs
        if epochs:
            epoch_df = pd.DataFrame(self.epochs)

        # Events
        if events:
            events_df = pd.DataFrame()
            for scorer in self.events:
                _event_df = pd.DataFrame()
                for event in self.events[scorer]:
                    _temp_df = pd.DataFrame(self.events[scorer][event])
                    _temp_df["Event"] = event
                    _temp_df["Scorer"] = scorer
                    _event_df = pd.concat(
                        [_event_df, _temp_df], axis=0, ignore_index=True, sort=False
                    )
                events_df = pd.concat(
                    [events_df, _event_df], axis=0, ignore_index=True, sort=False
                )

            if not events_df.empty:
                events_df["Time"] = events_df["Time"].apply(
                    lambda t: datetime.strptime(t[:-9], "%Y-%m-%dT%H:%M:%S.%f")
                )
                events_df["ElapsedTime"] = events_df["Time"] - self.start_time
                events_df["EpochNumber"] = events_df["ElapsedTime"].apply(
                    lambda x: int(ceil(x.seconds / 30))
                )
                epoch_seconds = events_df["ElapsedTime"].apply(
                    lambda x: (x - x.floor("30s"))
                )
                events_df["EpochTime"] = epoch_seconds.apply(
                    lambda y: float(".".join([str(y.seconds), str(y.microseconds)]))
                )

                ## Reset index and return
                events_df = events_df.sort_values(
                    ["EpochNumber", "Event", "Class", "Scorer"]
                )
                events_df = events_df.reset_index(drop=True)

            if "CustomEvents" in events_df["Event"].unique():
                custom_events = [
                    {"CEType": k, "CEName": self.custom_event_list[k]["name"]}
                    for k in self.custom_event_list.keys()
                ]
                custom_events_df = pd.DataFrame(custom_events)
                events_df = events_df.merge(custom_events_df, on="CEType")

        # Merge DataFrames
        output_df = pd.DataFrame()
        if not scoring_df.empty:
            output_df = scoring_df.copy()

        if epochs:
            if not epoch_df.empty:
                common_columns = list(set(output_df.columns) & set(epoch_df.columns))
                output_df = pd.merge(
                    output_df, epoch_df, how="outer", on=common_columns
                )

        if events:
            if not events_df.empty:
                common_columns = list(set(output_df.columns) & set(events_df.columns))
                output_df = pd.merge(
                    output_df, events_df, how="outer", on=common_columns
                )

        output_df = output_df.reset_index(drop=True)
        return output_df

## Remove later.  Just for testing purposes
