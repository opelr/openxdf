"""[summary]
"""

import xmltodict
import json
from collections import OrderedDict
import re

import pandas as pd


def read_data(fpath: str) -> OrderedDict:
    """Read XDF/JSON file and deidentify file
    
    Args:
        fpath (str): [description]
    
    Returns:
        OrderedDict: [description]
    """

    with open(fpath) as f:
        opened_file = f.read()
        xdf = xmltodict.parse(opened_file)

    ## Scrubs XDF of identifying information
    terms = ["xdf:FirstName", "xdf:LastName", "xdf:Comments"]
    for term in terms:
        xdf["xdf:OpenXDF"]["xdf:PatientInformation"][term] = None

    return xdf


def get_patient_ID(raw_data: OrderedDict):
    """[summary]
    """
    return str(raw_data["xdf:OpenXDF"]["xdf:PatientInformation"]["xdf:ID"])


def get_start_time(raw_data: OrderedDict):
    """Return PSG recording start time as a datetime object
    
    Args:
        raw_data (OrderedDict): [description]
    """
    try:
        session = self.raw_data["xdf:OpenXDF"]["xdf:DataFiles"]["xdf:DataFile"][
            "xdf:Sessions"
        ]["xdf:Session"]
    except TypeError:
        session = self.raw_data["xdf:OpenXDF"]["xdf:DataFiles"]["xdf:DataFile"][0][
            "xdf:Sessions"
        ]["xdf:Session"]

    return datetime.strptime(session["xdf:StartTime"][:-9], "%Y-%m-%dT%H:%M:%S.%f")


def clean_column_names(columns: list) -> list:
    """Remove 'nti:' and 'xdf:' motifs from a list
    
    Args:
        columns (list): List of stings that has displays the motif
    
    Returns:
        list: List of cleaned strings
    """
    return [re.sub("nti:|xdf:", "", ii) for ii in columns]


"""In-progress Section"""
# TODO: Consider making static method, or class inheritance from XDF
#       so that users only have to specify file & export paths.
def pretty_xml(raw_data, patient_ID: str, export_path: str):
    """Exports indented txt file for easier reading

    Args:
        raw_data (OrderedDict): [description]
        patient_ID (str): [description]
        export_path (str): [description]
    """
    export_file = export_path + patient_ID + "_pretty.txt"
    with open(export_file, "w") as pretty:
        pretty.write(json.dumps(raw_data, indent=4))


# TODO: Is this relevant for this module?
def compare_scores(self):
    """Compare sleep scoring between different sleep techs
        """
    all_stages = self.get_scoring()

    ## Casting indivStag to see if Scorers agree on staging
    comp_scores = all_stages.pivot(
        index="EpochNumber", columns="Scorer", values="Stage"
    )
    comp_scores["Agree"] = comp_scores.eq(comp_scores.iloc[:, 0], axis=0).all(1)
    comp_scores["ID"] = self.patient_ID
    comp_scores = pd.DataFrame(comp_scores.to_records())

    return comp_scores
