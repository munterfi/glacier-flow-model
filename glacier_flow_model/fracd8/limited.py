from typing import Tuple

import numpy as np
from numba import njit


@njit
def fracd8_lim(
    ele: np.ndarray, u: np.ndarray, h: np.ndarray, res: float
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Fraction D8 flow direction (limited)

    A modified version of the D8 algorithm for the flow direction of the water
    surface algorithm, which is able to determine the fraction of a cell that
    is moving based on an input velocity layer.

    Parameters
    ----------
    ele : np.ndarray
        Elevation array.
    u : np.ndarray
        Velocity array (v_max must be smaller than grid resolution).
    h : np.ndarray
        Height of the mass to flow.
    res : float
        Grid resolution, same unit range as u (e.g. meters).

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, str]
        New elevation of flow and the aspect D8 directions.

    """

    # Setup arrays
    asp = np.zeros_like(ele, dtype=np.uint8)
    h_flow = np.zeros_like(ele, dtype=np.float32)

    # Iterate through grid
    rows, cols = ele.shape
    for y in range(1, rows - 1):
        for x in range(1, cols - 1):
            pos = [
                (y, x),  # 0
                (y + 1, x + 1),  # 1
                (y, x + 1),  # 2
                (y - 1, x + 1),  # 3
                (y - 1, x),  # 4
                (y - 1, x - 1),  # 5
                (y, x - 1),  # 6
                (y + 1, x - 1),  # 7
                (y + 1, x),  # 8
            ]
            pos_0 = pos[0]

            # Classify aspect: Get steepest dz
            ele_0 = ele[pos_0]
            asp_0 = 0
            dz = 0
            for i in range(1, 9):
                dz_tmp = ele_0 - ele[pos[i]]
                if dz_tmp > dz:
                    asp_0 = i
                    dz = dz_tmp
            asp[pos_0] = asp_0

            # Flow
            h_0 = h[pos_0]
            if h_0 < 0.00001:
                # Nothing to flow!
                continue

            if asp_0 == 0:
                # Nowhere to flow!
                h_flow[pos_0] += h_0
                continue

            # Velocity defines fraction that stays in pixel (limited u!)
            u_0 = u[pos_0]
            fraction = min(u_0, 0.9999 * res) / res
            pos_i = pos[asp_0]
            h_flow[pos_0] += h_0 * (1 - fraction)
            h_flow[pos_i] += h_0 * fraction

    return h_flow, asp
