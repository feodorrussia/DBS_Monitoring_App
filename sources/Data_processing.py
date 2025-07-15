import numpy as np
import pandas as pd


def calc_magnitude(df: pd.DataFrame, time: bool = True) -> pd.DataFrame:
    """
    Calculate magnitude from df of complex data
    :param df: pd.DataFrame of the complex data
    :param time: is first column is **t** - time
    :return:
    """
    if time:
        sq_data = df.drop(["t"]).power(2).to_numpy().T
    else:
        sq_data = df.power(2).to_numpy().T

    magnitude = sq_data.reshape(-1, sq_data.shape[1], 2).sum(axis=2)

    if time:
        magnitude_df = pd.DataFrame(magnitude.T, columns=[f"ch{i}" for i in range(1, magnitude.shape[0] + 1)])
        return pd.concat([df.t, magnitude_df])

    return pd.DataFrame(magnitude.T, columns=[f"ch{i}" for i in range(1, magnitude.shape[0] + 1)])
