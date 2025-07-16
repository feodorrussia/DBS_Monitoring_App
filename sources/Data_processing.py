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


def calc_dPhase(df: pd.DataFrame, time: bool = True) -> pd.DataFrame:
    """
    Calculate first differential of the phase from df of complex data
    :param df: pd.DataFrame of the complex data
    :param time: is first column is **t** - time
    :return:
    """
    diff_timeline = None

    if time:
        point_data = df.drop(["t"], axis=1).to_numpy().reshape(-1, df.shape[1] // 2, 2)
        diff_timeline = pd.Series(np.linspace(start=df.t.min(), stop=df.t.max(), num=df.shape[0] - 1))
    else:
        point_data = df.to_numpy().reshape(-1, df.shape[1] // 2, 2)

    z_data = point_data[:, :, 0] + 1j * point_data[:, :, 1]
    d_phase_data = np.diff(np.unwrap(np.angle(z_data), axis=0), axis=0)

    if time:
        d_phase_df = pd.DataFrame(d_phase_data, columns=[f"ch{i}" for i in range(1, d_phase_data.shape[1] + 1)])
        return pd.concat([diff_timeline, d_phase_df], axis=1).rename({"0": "t"})

    return pd.DataFrame(d_phase_data, columns=[f"ch{i}" for i in range(1, d_phase_data.shape[1] + 1)])
