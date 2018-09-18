"""Command-line module for XDF conversion

Example: python3-64 polysmith\openxdf\convert_xdf.py -i 
"""

import argparse
# import pandas as pd
from xdf_class import XDF

## Command Line Argument parsing
parser = argparse.ArgumentParser(description="Convert decrypted OpenXDF file to CSV")
required_args = parser.add_argument_group("required arguments")
required_args.add_argument("-i", "--input", help="Input file path", required=True)
required_args.add_argument(
    "-o", "--output", help="Output file parent folder", required=True
)
args = parser.parse_args()

## Read and Convert xdf file
def convert_xdf(input_file, output_folder):
    x = XDF(input_file)
    out_data = x.data
    out_data["StartTime"] = x.start_time

    file_name = x.patient_ID
    output_destination = output_folder.rstrip("/") + "/" + file_name + ".csv"
    out_data.to_csv(output_destination)


if __name__ == "__main__":
    convert_xdf(args.input, args.output)
    print("  XDF conversion complete")
