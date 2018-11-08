"""
openxdf.helpers
~~~~~~~~~~~~~~~

Helper functions
"""

from datetime import datetime
import re
import pandas as pd


def start_time(xdf):
    data_file = xdf._data["xdf:DataFiles"]["xdf:DataFile"]

    if type(data_file) is dict:
        session = data_file["xdf:Sessions"]["xdf:Session"]
    elif type(data_file) is list:
        session = data_file[0]["xdf:Sessions"]["xdf:Session"]
    else:
        raise TypeError

    return datetime.strptime(session["xdf:StartTime"][:-9], "%Y-%m-%dT%H:%M:%S.%f")


def pull_header(xdf):
    header = {}
    data_file = xdf._data["xdf:DataFiles"]["xdf:DataFile"]

    header["id"] = re.sub("[.]nkamp", "", data_file["xdf:File"])
    header["epoch_length"] = int(xdf._data["xdf:EpochLength"])
    header["frame_length"] = int(data_file["xdf:FrameLength"])
    header["endian"] = data_file["xdf:Endian"]
    header["file"] = data_file["xdf:File"]

    return header


def pull_sources(xdf):
    sources = xdf._data["xdf:DataFiles"]["xdf:DataFile"]["xdf:Sources"]["xdf:Source"]

    for source in sources:
        for k, v in source.items():
            new_key = clean_title(k)
            source[new_key] = source.pop(k)

            if re.match("[0-9]+[\.e][-]?[0-9]+", str(v)) is not None:
                source[new_key] = float(str(v))
            elif re.match("[0-9]+", str(v)) is not None:
                source[new_key] = int(str(v))

    return sources


def pull_epochs(xdf):
    """Extract epoch information from raw data
        
    Returns:
        dict: Dict with epoch information
    """
    if "xdf:ScoringResults" not in xdf._data.keys():
        return {}

    epochs = xdf._data["xdf:ScoringResults"]["xdf:EpochInformation"]["xdf:Epoch"]
    for epoch in epochs:
        for k, v in epoch.items():
            new_key = clean_title(k)
            epoch[new_key] = epoch.pop(k)

            if re.match("[0-9]+[\.|e][-]?[0-9]+", str(v)) is not None:
                epoch[new_key] = float(v)
            elif re.match("[0-9]+", str(v)) is not None:
                epoch[new_key] = int(v)

    return epochs


def pull_scoring(xdf):
    if "xdf:ScoringResults" not in xdf._data.keys():
        return {}

    scoring_info = []

    scorers = xdf._data["xdf:ScoringResults"]["xdf:Scorers"]["xdf:Scorer"]
    for scorer in scorers:
        header = {}
        header["first_name"] = scorer["xdf:FirstName"]
        header["last_name"] = scorer["xdf:LastName"]

        staging = {}
        for epoch in scorer["xdf:SleepStages"]["xdf:SleepStage"]:
            staging[epoch["xdf:EpochNumber"]] = epoch["xdf:Stage"]

        scoring_info.append({"header": header, "staging": staging})

    return scoring_info


def pull_custom_event_list(xdf):
    custom_events = {}

    scorers = xdf._data["xdf:ScoringResults"]["xdf:Scorers"]["xdf:Scorer"]
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


def pull_events(xdf):
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

    scorers = xdf._data["xdf:ScoringResults"]["xdf:Scorers"]["xdf:Scorer"]
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


def create_dataframe(xdf, epochs=True, events=True):
    if epochs:
        epoch_df = pd.DataFrame(xdf.epochs)
    # TODO: Unpack openxdf.events and openxdf.scoring dicts into dataframes
    raise NotImplementedError


def clean_title(title: str) -> str:
    """Remove 'nti:' and 'xdf:' motifs from a str
    
    Args:
        title (str): Single string with motif
    
    Returns:
        str: Cleaned string
    """
    return re.sub("nti:|xdf:", "", title)
