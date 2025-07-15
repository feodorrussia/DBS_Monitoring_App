import numpy as np
import pandas as pd
import os

import shtReader_py.shtRipper as shtRipper


def load_sht(file_path: str, column_names: list = None, data_names: list = None) -> pd.DataFrame:
    """
    Function to load data from .SHT files. Use shtRipper.ripper.read() from shtReader_py.
    :param file_path: name of the file with **absolute** path
    :param column_names: (optional) list of column names that need to be loaded
    :param data_names: (optional) list of data names to rename loaded columns
    :return: pd.DataFrame with all or selected (if columns_names defined) columns
    """
    if ".sht" in file_path.lower():
        if not os.path.isfile(file_path):
            raise FileNotFoundError
        res = shtRipper.ripper.read(file_path)
    else:
        if not os.path.isfile(file_path + ".SHT"):
            raise FileNotFoundError
        res = shtRipper.ripper.read(file_path + ".SHT")

    if column_names is None:
        column_names = res.keys()

    if data_names is None:
        data_names = column_names
    elif len(data_names) != len(column_names):
        raise ValueError("Number of columns & names does not match")

    data = np.array([res[column_names[0]]["x"]] + [res[column_name]["y"] for column_name in column_names])
    dalpha_df = pd.DataFrame(data.transpose(), columns=["t"] + data_names)
    return dalpha_df


def save_df_to_txt(df: pd.DataFrame, file_name: str, file_path: str, meta: str = None) -> None:
    """
    Function to save a dataframe to a text file with additional meta info.
    :param file_name: file name of saving file
    :param df: pd.DataFrame to save
    :param file_path: path to save data
    :param meta: (optional) additional meta info
    :return:
    """
    file_path_name = file_path + file_name + ".txt"
    pd_save_mode = "w"
    if meta is not None:
        line_width = 25
        printed_meta = meta  # formating meta for good-looking
        with open(file_path_name, "w") as text_file:
            text_file.write(printed_meta + "\n" + "=" * line_width + "\n")
            text_file.close()
        pd_save_mode = "a"

    df.to_csv(file_path, index=False, mode=pd_save_mode)
