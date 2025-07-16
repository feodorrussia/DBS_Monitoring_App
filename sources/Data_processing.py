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
        point_data = df.drop(["t"], axis=1).to_numpy().reshape(-1, df.shape[1] // 2, 2)
    else:
        point_data = df.to_numpy().reshape(-1, df.shape[1] // 2, 2)

    z_data = point_data[:, :, 0] + 1j * point_data[:, :, 1]
    magnitude = np.abs(z_data)

    if time:
        magnitude_df = pd.DataFrame(magnitude, columns=[f"ch{i}" for i in range(1, magnitude.shape[1] + 1)])
        return pd.concat([df.t, magnitude_df], axis=1).rename({"0": "t"})

    return pd.DataFrame(magnitude, columns=[f"ch{i}" for i in range(1, magnitude.shape[1] + 1)])
