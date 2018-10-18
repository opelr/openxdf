"""Pretty printing for OpenXDF files

Example: `python3 polysmith\openxdf\pretty_xdf.py -i tests\data\RBD_Scored.xdf -o tests\data\`"""

import json
import xmltodict
import argparse

from .helpers import read_data, get_patient_ID, pretty_xml

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


def PrettyPrintXDF(input_path, output_path):
    raw_data = read_data(input_path)
    patient_ID = get_patient_ID(raw_data)
    pretty_xml(raw_data, patient_ID, output_path)


if __name__ == "__main__":
    PrettyPrintXDF(args.input, args.output)
    print("-- XDF Pretty Printing complete --")
