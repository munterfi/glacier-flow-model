import numpy as np
from .infinite import fracd8_inf
from .limited import fracd8_lim

from numba import njit


@njit
def fracd8(ele: np.ndarray, u: np.ndarray, h: np.ndarray, res: float):
    mode = "limited"
    if u.max() < res:
        h_flow, asp = fracd8_lim(ele, u, h, res)
    else:
        mode = "infinite"
        h_flow, asp = fracd8_inf(ele, u, h, res)
    return h_flow, asp, mode
