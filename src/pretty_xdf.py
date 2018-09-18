"""Pretty printing for OpenXDF files

Example: `python3 polysmith\openxdf\pretty_xdf.py -i tests\data\RBD_Scored.xdf -o tests\data\`"""

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


def PrettyPrintXDF(input_path, output_path):
    def read_data(input_path):
        """Read XDF/JSON file and deidentify file"""
        with open(input_path) as f:
            opened_file = f.read()
            xdf = xmltodict.parse(opened_file)

        ## Scrubs XDF of identifying information
        terms = ["xdf:FirstName", "xdf:LastName", "xdf:Comments"]
        for term in terms:
            xdf["xdf:OpenXDF"]["xdf:PatientInformation"][term] = None

        return xdf

    def get_patient_ID(raw_data):
        pat_ID = str(raw_data["xdf:OpenXDF"]["xdf:PatientInformation"]["xdf:ID"])
        return pat_ID

    def pretty_xml(output_path, patient_ID, raw_data):
        """Exports indented txt file for easier reading"""
        export_file = output_path + patient_ID + "_pretty.txt"
        with open(export_file, "w") as pretty:
            pretty.write(json.dumps(raw_data, indent=4))

    raw_data = read_data(input_path)
    patient_ID = get_patient_ID(raw_data)
    pretty_xml(output_path, patient_ID, raw_data)


if __name__ == "__main__":
    PrettyPrintXDF(args.input, args.output)
    print("-- XDF Pretty Printing complete --")
