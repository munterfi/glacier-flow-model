import numpy as np


def hillshade(array: np.ndarray, azimuth: int, altitude: int) -> np.ndarray:
    """
    Render hillshade

    Calculates a shaded relief from a digital elevation model (DEM) input.

    Parameters
    ----------
    array : np.ndarray
        Digital elevation model.
    azimuth : int
        Direction of the illumination source.
    altitude : int
        Altitude of illumination source

    Returns
    -------
    np.ndarray
        The rendered hillshade.

    """
    x, y = np.gradient(array, 22, 22)
    slope = np.pi / 2.0 - np.arctan(np.sqrt(x * x + y * y))
    x, y = np.gradient(array, 3, 3)
    aspect = np.arctan2(-y, x)
    azimuth_rad = azimuth * np.pi / 180.0
    altitude_rad = altitude * np.pi / 180.0

    shaded = np.sin(altitude_rad) * np.sin(slope) + np.cos(altitude_rad) * np.cos(
        slope
    ) * np.cos(azimuth_rad - aspect)

    return 255 * (shaded + 1) / 2
