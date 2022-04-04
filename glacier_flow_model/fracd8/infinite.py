from typing import Tuple

import numpy as np
from numba import njit
from numba import prange


@njit
def position(x: int, y: int, n: int) -> Tuple[int, int]:
    """D8 position in array

    Returns the position in an array based on the D8 directions.

     --- --- ---
    | 7 | 8 | 1 |
     --- --- ---
    | 6 | 0 | 2 |
     --- --- ---
    | 5 | 4 | 3 |
     --- --- ---

    Parameters
    ----------
    x : int
        Coord x of origin.
    y : int
        Coord y of origin.
    n : int
        D8 direction.

    Returns
    -------
    Tuple[int, int]
        Index of D8 direction.

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
    """Classified aspect

    Calculates the steepest dz and returns the result as D8 direction.
    Note: Do not use position() inside this function for performance reasons!
    Seems the JIT compiler is better in optimizing the solution below.

    Parameters
    ----------
    ele : np.ndarray
        Elevation array.

    Returns
    -------
    np.ndarray
        D8 direction array.

    """

    ele = ele.astype(np.float32)
    asp = np.zeros_like(ele, dtype=np.uint8)
    asp[:] = np.nan

    rows, cols = ele.shape
    for y in range(1, rows - 1):
        for x in range(1, cols - 1):

            # Replace position function
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
    ele: np.ndarray, u: np.ndarray, h: np.ndarray, res: float, max_offset: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Fraction D8 flow direction (infinite)

    A modified version of the D8 algorithm for the flow direction of the water
    surface algorithm, which is able to determine the fraction of a cell that
    is moving based on an input velocity layer. When moving in interations on a
    grid, there is a fundamental problem: What happens when the distance of the
    movement in one iteration exceeds the grid resolution?

    In this case, the implemented solution will follow the flow in the cells via
    the classified aspect until the necessary distance is reached. This neglects
    the flow of other cells into the followed cells, which would have changed the
    aspect and thereby the direction of flow. In addition, the performance is
    worse.

    Parameters
    ----------
    ele : np.ndarray
        Elevation array.
    u : np.ndarray
        Velocity array.
    h : np.ndarray
        Height of the mass to flow.
    res : float
        Grid resolution, same unit range as u (e.g. meters).
    max_offset : int, optional
        Maximum number of steps to follow the flow in cells with u > res,
        by default 3

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, str]
        New elevation of flow and the aspect D8 directions.

    """

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
            offset = min(int(frac), max_offset)

            # Follow the aspect during offset
            x_i = x
            y_i = y
            for _ in range(offset):
                asp_step = asp[y_i, x_i]
                y_i, x_i = position(x_i, y_i, asp_step)

            # Add flow to destination-1 and destination cell
            frac_share = frac - int(frac)
            h_flow[y_i, x_i] += h_0 * (1 - frac_share)
            h_flow[position(x_i, y_i, asp[y_i, x_i])] += h_0 * frac_share

    return h_flow, asp
