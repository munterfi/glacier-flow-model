from typing import Tuple

import numpy as np
from numba import njit

from .direction import classify_aspect
from .direction import position


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
    asp = classify_aspect(ele)

    # Setup array
    h_flow = np.zeros_like(asp, dtype=np.float32)

    # Iterate through grid
    rows, cols = asp.shape
    for y in range(1, rows - 1):
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
            fraction = u_0 / res
            share = fraction - int(fraction)
            offset = min(int(fraction), max_offset)

            # Follow the aspect during offset
            x_i = x
            y_i = y
            for _ in range(offset):
                asp_step = asp[y_i, x_i]
                y_i, x_i = position(x_i, y_i, asp_step)

            # Add flow to destination-1 and destination cell
            h_flow[y_i, x_i] += h_0 * (1 - share)
            h_flow[position(x_i, y_i, asp[y_i, x_i])] += h_0 * share

    return h_flow, asp
