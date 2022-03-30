from typing import Tuple

import numpy as np
from numba import njit
from numba import prange


@njit
def position(x: int, y: int, n: int) -> Tuple[int, int]:
    """
     --- --- ---
    | 7 | 8 | 1 |
     --- --- ---
    | 6 | 0 | 2 |
     --- --- ---
    | 5 | 4 | 3 |
     --- --- ---
    """
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
    pos_n = pos[n]
    return pos_n


@njit
def aspect(ele: np.ndarray) -> np.ndarray:
    """
    DO NOT USE d8_position() for performance reasons!
    """
    ele = ele.astype(np.float32)
    asp = np.zeros_like(ele, dtype=np.uint8)
    asp[:] = np.nan

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

    return asp


@njit
def fracd8_inf(
    ele: np.ndarray, u: np.ndarray, h: np.ndarray, res: float
) -> Tuple[np.ndarray, np.ndarray]:

    # Get aspect
    asp = aspect(ele)

    # Setup array
    h_flow = np.zeros_like(asp, dtype=np.float32)

    # Iterate through grid
    rows, cols = asp.shape
    for y in prange(1, rows - 1):
        for x in range(1, cols - 1):
            pos_0 = position(x, y, 0)

            # Flow
            h_0 = h[pos_0]
            if h_0 < 0.00001:
                # Nothing to flow!
                continue

            asp_0 = asp[pos_0]
            if asp_0 == 0:
                # Nowhere to flow!
                h_flow[pos_0] += h_0
                continue

            # Velocity defines fraction that stays in pixel
            u_0 = u[pos_0]
            frac = u_0 / res
            offset = int(frac)

            # Follow the aspect during offset
            x_i = x
            y_i = y
            for _ in range(offset):
                asp_step = asp[y_i, x_i]
                y_i, x_i = position(x_i, y_i, asp_step)

            # Add flow to destination-1 and destination cell
            frac = frac - offset
            h_flow[y_i, x_i] += h_0 * (1 - frac)
            h_flow[position(x_i, y_i, asp[y_i, x_i])] += h_0 * frac

    return h_flow, asp
