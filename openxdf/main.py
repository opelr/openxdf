"""DOCSTRING"""

import pandas as pd
from pathlib import PurePath
import glob
from xdf_class import XDF


def glob_path(path):
    p = PurePath(path)
    extension = "*.xdf"
    path_str = str(p / extension)
    all_files = glob.glob(path_str)
    return all_files


def main(file_list):
    """Map XDF class to all files passed in `file_list`, then return dataframe"""
    main_df = pd.DataFrame()

    for fil in file_list:
        print(fil.split("\\")[-1])
        try:
            x = XDF(fil)
        except:
            print("------ BAD ------")
            continue
        main_df = main_df.append(x.data, ignore_index=True)

    return main_df


if __name__ == "__main__":
    file_path = "D:\data\processed_data\human\h4108\PSG\XDF\Dennis"
    all_files = glob_path(file_path)
    bad_files = ["XAXVDJYND8L97Y7.xdf", "XAXVDF7ZK8LNVI6.xdf", "XVZ2FF9YJ8T4C0E.xdf"]
    bad_paths = [file_path + "\\" + i for i in bad_files]
    good_files = [i for i in all_files if i not in bad_paths]

    main_df = main(good_files)
    main_df.to_csv("data/2018-06-08_XDF-Data.csv")
