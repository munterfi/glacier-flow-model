from typing import Tuple

import numpy as np
from numba import njit

from .infinite import fracd8_inf
from .limited import fracd8_lim


@njit
def fracd8(
    ele: np.ndarray, u: np.ndarray, h: np.ndarray, res: float, max_offset: int = 5
) -> Tuple[np.ndarray, np.ndarray, str]:
    """
    Fraction D8 flow direction

    A modified version of the D8 algorithm for the flow direction of the water
    surface algorithm, which is able to determine the fraction of a cell that
    is moving based on an input velocity layer.

    Decides after a check of the maxium velocity, which version to choose:
    'fracd8_lim' (better performance) or 'fracd8_inf' for velocities larger than
    the grid resolution.

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
        by default 5

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, str]
        New elevation of flow, the aspect D8 directions, used mode.

    """
    mode = "limited"
    if max_offset < 1 or u.max() < res:
        h_flow, asp = fracd8_lim(ele, u, h, res)
    else:
        mode = "infinite"
        h_flow, asp = fracd8_inf(ele, u, h, res, max_offset)
    return h_flow, asp, mode
