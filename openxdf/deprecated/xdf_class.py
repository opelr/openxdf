"""Functions related to processing Polysmith's openXDF files.

This module contains a handful of functions that assist with
processing, decryption, saving, and analyzing Polysmith's PSG files, in
openXDF file format.
"""

import re
import math
import pandas as pd
from datetime import datetime, timedelta

from .helpers import read_data, get_patient_ID, get_start_time, clean_column_names

## TODO: Fix the try/except calls; no such thing as a 'bad file'


class XDF:
    """Class wrapper for extracting data from `.xdf` files"""

    def __init__(self, filepath):
        self._fpath = filepath
        self._raw_data = read_data(self._fpath)
        self.patient_ID = get_patient_ID(self._raw_data)
        self.start_time = get_start_time(self._raw_data)
        self.data = self._merge_dataframes()

    def __repr__(self):
        return f"XDF file({self.patient_ID!r})"

    def _get_epochs(self) -> pd.DataFrame:
        """Extract epoch information from raw data
        
        Returns:
            pd.DataFrame: DataFrame with epoch information
        """
        try:
            epoch = self.raw_data["xdf:OpenXDF"]["xdf:ScoringResults"][
                "xdf:EpochInformation"
            ]["xdf:Epoch"]
        except TypeError:
            epoch, epoch_DF = [None, None]

        if epoch is not None:
            epoch_DF = pd.DataFrame.from_dict(epoch)
            epoch_DF["xdf:EpochNumber"] = pd.to_numeric(epoch_DF["xdf:EpochNumber"])
            epoch_DF["ID"] = self.patient_ID

            ## Indexing and housekeeping
            epoch_DF.columns = clean_column_names(epoch_DF.columns)
            epoch_DF = epoch_DF.sort_values("EpochNumber")
            epoch_DF.reset_index(inplace=True, drop=True)

        return epoch_DF

    def _get_scoring(self) -> pd.DataFrame:
        """Extract sleep scoring information from raw data
        
        Returns:
            pd.DataFrame: DataFrame with sleep scoring information
        """

        all_stages = pd.DataFrame()

        # List of all sleep techs that scored the PSG
        scorers = self.raw_data["xdf:OpenXDF"]["xdf:ScoringResults"]["xdf:Scorers"]
        if type(scorers["xdf:Scorer"]) is list:
            # If there's only one scorer (i.e. type is dict), it's PolySmith and I want to skip
            for scorer in scorers["xdf:Scorer"]:
                scorer_name = scorer["xdf:FirstName"]
                if scorer_name != "Polysmith":
                    stages = pd.DataFrame.from_dict(
                        scorer["xdf:SleepStages"]["xdf:SleepStage"]
                    )
                    stages["xdf:EpochNumber"] = pd.to_numeric(stages["xdf:EpochNumber"])
                    stages = stages.sort_values("xdf:EpochNumber")
                    stages["Scorer"] = scorer_name
                    all_stages = all_stages.append(stages)

        if not all_stages.empty:
            all_stages.columns = clean_column_names(all_stages.columns)
            all_stages = all_stages.drop(["InfStage", "StgStrength"], 1)
            all_stages = all_stages.sort_values("EpochNumber")
            all_stages.reset_index(inplace=True, drop=True)

        return all_stages

    def _list_custom_events(self) -> pd.DataFrame:
        """Create custom event indexing dictionary
        
        Returns:
            pd.DataFrame: [description]
        """

        ce_config = pd.DataFrame()
        scorers = self.raw_data["xdf:OpenXDF"]["xdf:ScoringResults"]["xdf:Scorers"]

        for scorer in scorers["xdf:Scorer"]:
            try:
                temp_ce_DF = pd.DataFrame(scorer["nti:CEConfigs"]["nti:CEConfig"])
            except TypeError:
                temp_ce_DF = None
            ce_config = pd.concat([ce_config, temp_ce_DF])

        if not ce_config.empty:
            ce_config.columns = clean_column_names(ce_config.columns)
            ce_config = ce_config[["CEType", "CEName"]]
            ce_config = ce_config.drop_duplicates()
            ce_config = ce_config.sort_values(["CEType"])
            ce_config.reset_index(inplace=True, drop=True)
        return ce_config

    def _get_events(self):
        """Strip all custom events"""
        event_DF = pd.DataFrame()

        scorers = self.raw_data["xdf:OpenXDF"]["xdf:ScoringResults"]["xdf:Scorers"]
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

        def _internal_event_fn(scorer, parent_DF, sections):
            scorer_name = scorer["xdf:FirstName"]
            for k, v in sections:
                try:
                    tempDF = pd.DataFrame(scorer[k][v])
                    tempDF["Event"] = re.sub("xdf:|nti:", "", v)
                    tempDF["Scorer"] = scorer_name
                except (ValueError, TypeError):
                    tempDF = None

                parent_DF = pd.concat([parent_DF, tempDF], sort=True)
            return parent_DF

        ### If there are multiple scorers
        if type(scorers["xdf:Scorer"]) is list:
            for scorer in scorers["xdf:Scorer"]:
                event_DF = _internal_event_fn(scorer, event_DF, sections)
        else:
            scorer = scorers["xdf:Scorer"]
            event_DF = _internal_event_fn(scorer, event_DF, sections)

        ## Indexing and housekeeping
        if not event_DF.empty:
            event_DF.columns = clean_column_names(event_DF.columns)
            event_DF["Time"] = event_DF["Time"].apply(
                lambda t: datetime.strptime(t[:-9], "%Y-%m-%dT%H:%M:%S.%f")
            )
            event_DF = event_DF.sort_values(["Event", "Scorer", "Time"])

        ## Merge Custom Events (CEs) after verifying that a) there were any CEs
        ## defined, and b) there are some CEs scored
        custom_event_key = self._list_custom_events()
        if (not custom_event_key.empty) and ("CEType" in event_DF.columns):
            event_DF = event_DF.merge(custom_event_key, on="CEType", how="left")
            ### Rename Event column by Custom Event when CE name is available
            event_DF.loc[event_DF["CEName"].notnull(), "Event"] = event_DF["CEName"]
            event_DF = event_DF.drop(["CEType", "CEName"], axis=1)

        ## Determine Epoch Number from ClockTime
        ### Calculate Epoch from ElapsedTime
        if not event_DF.empty:
            event_DF["ElapsedTime"] = event_DF["Time"] - self.start_time
            event_DF["EpochNumber"] = event_DF["ElapsedTime"].apply(
                lambda x: int(math.ceil(x.seconds / 30))
            )

        ## Reset index and return
        event_DF.reset_index(inplace=True, drop=True)
        return event_DF

    # TODO: Fix what gets exported -- should depend on availability of different DF's
    def _merge_dataframes(self):
        """Calls all data-stripping functions, merges and returns single pd.DF"""
        epoch_DF = self._get_epochs()
        scoring_DF = self._get_scoring()
        event_DF = self._get_events()

        if epoch_DF is None or epoch_DF.empty or scoring_DF is None or scoring_DF.empty:
            return pd.DataFrame()

        merge_df_1 = scoring_DF.merge(
            event_DF, on=["EpochNumber", "Scorer"], how="left"
        )
        merge_df_2 = merge_df_1.merge(epoch_DF, on="EpochNumber", how="left")
        merge_df_2.reset_index(inplace=True, drop=True)

        return merge_df_2
