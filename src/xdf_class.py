"""Functions related to processing Polysmith's openXDF files.

This module contains a handful of functions that assist with
processing, decryption, saving, and analyzing Polysmith's PSG files, in
openXDF file format.
"""

import re
import json
import xmltodict
import math
import pandas as pd
from datetime import datetime, timedelta

## TODO: Fix the try/except calls; no such thing as a 'bad file'


class XDF:
    """Class wrapper for extracting data from `.xdf` files"""

    def __init__(self, filepath):
        self.filepath = filepath
        self.raw_data = self.read_data()
        self.patient_ID = self.get_patient_ID()
        self.start_time = self.get_start_time()
        self.data = self._merge_dataframes()

    def __repr__(self):
        return f"XDF file({self.patient_ID!r})"

    def read_data(self):
        """Read XDF/JSON file and deidentify file"""
        with open(self.filepath) as f:
            _, extension = self.filepath.split(".")
            if extension == "json":
                xdf = json.load(f)
            elif extension == "xdf":
                opened_file = f.read()
                xdf = xmltodict.parse(opened_file)

        ## Scrubs XDF of identifying information
        terms = ["xdf:FirstName", "xdf:LastName", "xdf:Comments"]
        for term in terms:
            xdf["xdf:OpenXDF"]["xdf:PatientInformation"][term] = None

        return xdf

    def get_patient_ID(self):
        pat_ID = str(self.raw_data["xdf:OpenXDF"]["xdf:PatientInformation"]["xdf:ID"])
        return pat_ID

    def save_json(self, export_path):
        export_file = export_path + self.patient_ID + ".json"
        with open(export_file, "w") as json_export:
            json.dump(self.raw_data, json_export)

    # @staticmethod
    def pretty_xml(self, export_path):
        """Exports indented txt file for easier reading"""
        export_file = export_path + self.patient_ID + "_pretty.txt"
        with open(export_file, "w") as pretty:
            pretty.write(json.dumps(self.raw_data, indent=4))

    def get_start_time(self):
        try:
            session = self.raw_data["xdf:OpenXDF"]["xdf:DataFiles"]["xdf:DataFile"][
                "xdf:Sessions"
            ]["xdf:Session"]
        except TypeError:
            session = self.raw_data["xdf:OpenXDF"]["xdf:DataFiles"]["xdf:DataFile"][0][
                "xdf:Sessions"
            ]["xdf:Session"]
        start_time = datetime.strptime(
            session["xdf:StartTime"][:-9], "%Y-%m-%dT%H:%M:%S.%f"
        )
        return start_time

    def get_epochs(self):
        """Strip raw epoch information"""
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
            epoch_DF.columns = [re.sub("nti:|xdf:", "", ii) for ii in epoch_DF.columns]
            epoch_DF = epoch_DF.sort_values("EpochNumber")
            epoch_DF.reset_index(inplace=True, drop=True)

        return epoch_DF

    def get_scoring(self):
        """Strip sleep scoring information"""
        all_stages = pd.DataFrame()

        ## List of all sleep techs that scored the PSG
        scorers = self.raw_data["xdf:OpenXDF"]["xdf:ScoringResults"]["xdf:Scorers"]

        if type(scorers["xdf:Scorer"]) is list:
            """If there's only one scorer (i.e. type is dict), it's PolySmith and I want to skip"""
            for scorer in scorers["xdf:Scorer"]:
                scorer_name = scorer["xdf:FirstName"]
                if scorer_name == "Polysmith":
                    pass
                else:
                    stages = pd.DataFrame.from_dict(
                        scorer["xdf:SleepStages"]["xdf:SleepStage"]
                    )
                    stages["xdf:EpochNumber"] = pd.to_numeric(stages["xdf:EpochNumber"])
                    stages = stages.sort_values("xdf:EpochNumber")
                    stages["Scorer"] = scorer_name

                    all_stages = all_stages.append(stages)

        if not all_stages.empty:
            all_stages.columns = [
                re.sub("nti:|xdf:", "", ii) for ii in all_stages.columns
            ]
            all_stages = all_stages.drop(["InfStage", "StgStrength"], 1)
            all_stages = all_stages.sort_values("EpochNumber")
            all_stages.reset_index(inplace=True, drop=True)
        return all_stages

    def compare_scores(self):
        """Compare sleep scoring between different sleep techs"""
        all_stages = self.get_scoring()

        ## Casting indivStag to see if Scorers agree on staging
        comp_scores = all_stages.pivot(
            index="EpochNumber", columns="Scorer", values="Stage"
        )
        comp_scores["Agree"] = comp_scores.eq(comp_scores.iloc[:, 0], axis=0).all(1)
        comp_scores["ID"] = self.patient_ID
        comp_scores = pd.DataFrame(comp_scores.to_records())

        return comp_scores

    def _custom_events(self):
        """Create custom event indexing dictionary"""
        ce_config = pd.DataFrame()
        scorers = self.raw_data["xdf:OpenXDF"]["xdf:ScoringResults"]["xdf:Scorers"]

        for scorer in scorers["xdf:Scorer"]:
            try:
                temp_ce_DF = pd.DataFrame(scorer["nti:CEConfigs"]["nti:CEConfig"])
            except TypeError:
                temp_ce_DF = None
            ce_config = pd.concat([ce_config, temp_ce_DF])

        if not ce_config.empty:
            ce_config.columns = [
                re.sub("nti:|xdf:", "", ii) for ii in ce_config.columns
            ]
            ce_config = ce_config[["CEType", "CEName"]]
            ce_config = ce_config.drop_duplicates()
            ce_config = ce_config.sort_values(["CEType"])
            ce_config.reset_index(inplace=True, drop=True)
        return ce_config

    def get_events(self):
        """Strip all custom events"""
        event_DF = pd.DataFrame()
        scorers = self.raw_data["xdf:OpenXDF"]["xdf:ScoringResults"]["xdf:Scorers"]
        sections = {
            "xdf:Apneas": "xdf:Apnea",
            "xdf:Hypopneas": "xdf:Hypopnea",
            "xdf:Desaturations": "xdf:Desaturation",
            "xdf:Microarousals": "xdf:Microarousal",
            "xdf:Snores": "xdf:Snore",
            "xdf:LegMovements1": "xdf:LegMovement",
            "xdf:LegMovements2": "xdf:LegMovement",
            "nti:CustomEvents": "nti:CustomEvent",
        }

        def _internal_event_fn(scorer, parent_DF, sections):
            scorer_name = scorer["xdf:FirstName"]
            for k, v in sections.items():
                try:
                    tempDF = pd.DataFrame(scorer[k][v])
                    tempDF["Event"] = re.sub("xdf:|nti:", "", v)
                    tempDF["Scorer"] = scorer_name
                except (ValueError, TypeError):
                    tempDF = None

                parent_DF = pd.concat([parent_DF, tempDF])
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
            event_DF.columns = [re.sub("nti:|xdf:", "", ii) for ii in event_DF.columns]
            event_DF["Time"] = event_DF["Time"].apply(
                lambda t: datetime.strptime(t[:-9], "%Y-%m-%dT%H:%M:%S.%f")
            )
            event_DF = event_DF.sort_values(["Event", "Scorer", "Time"])

        ## Merge Custom Events (CEs) after verifying that a) there were any CEs
        ## defined, and b) there are some CEs scored
        custom_event_key = self._custom_events()
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
        epoch_DF = self.get_epochs()
        scoring_DF = self.get_scoring()
        event_DF = self.get_events()

        if epoch_DF is None or epoch_DF.empty or scoring_DF is None or scoring_DF.empty:
            merge_2 = pd.DataFrame()
        else:
            merge_1 = scoring_DF.merge(
                event_DF, on=["EpochNumber", "Scorer"], how="left"
            )
            merge_2 = merge_1.merge(epoch_DF, on="EpochNumber", how="left")
            merge_2.reset_index(inplace=True, drop=True)

        return merge_2
