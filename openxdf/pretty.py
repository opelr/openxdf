# -*- coding: utf-8 -*-

"""
openxdf.pretty
~~~~~~~~~~~~~~

Pretty printing for OpenXDF files.
"""

import json
import xmltodict
import argparse


## Command Line Argument parsing
parser = argparse.ArgumentParser(
    description="Print decrypted OpenXDF files in a pretty, human-readable way"
)
required_args = parser.add_argument_group("required arguments")
required_args.add_argument("-i", "--input", help="Input file path", required=True)
required_args.add_argument(
    "-o", "--output", help="Output file parent folder", required=True
)
args = parser.parse_args()


def main(ipath: str, opath: str):
    with open(ipath, "r") as f:
        xdf_odict = xmltodict.parse(f.read())
    
    xdf = json.loads(json.dumps(xdf_odict))
    
    terms = ["xdf:FirstName", "xdf:LastName", "xdf:DOB", "xdf:Comments"]
    for term in terms:
        xdf["xdf:OpenXDF"]["xdf:PatientInformation"][term] = None
    
    with open(opath, "w") as o:
       o.write(json.dumps(xdf, indent=4))


if __name__ == "__main__":
    main(args.input, args.output)
