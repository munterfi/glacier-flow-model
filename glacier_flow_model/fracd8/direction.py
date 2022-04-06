from typing import Tuple

import numpy as np
from numba import njit


@njit
def position(x: int, y: int, n: int) -> Tuple[int, int]:
    """
    D8 position in array

    Returns the position in an array based on the D8 directions.

    +---+---+---+
    | 7 | 8 | 1 |
    +---+---+---+
    | 6 | 0 | 2 |
    +---+---+---+
    | 5 | 4 | 3 |
    +---+---+---+

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
def classify_aspect(ele: np.ndarray) -> np.ndarray:
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
