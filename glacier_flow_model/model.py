"""The glacier flow model and visualization."""
from ast import Str
from logging import getLogger
from pathlib import Path
from re import search
from typing import Optional

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from osgeo.gdal import GDT_Float32
from osgeo.gdal import GetDriverByName
from osgeo.gdal import Open
from scipy.ndimage import gaussian_filter
from scipy.ndimage import uniform_filter

LOG = getLogger(__name__)

# Disable toolbar
mpl.rcParams["toolbar"] = "None"


class GlacierFlowModel:
    """Class for modeling glacier flow."""

    MODEL_RANDOM_NUDGING = True
    PLOT_FRAME_RATE = 5
    PLOT_WIDTH = 15
    PLOT_HEIGHT = 5
    PLOT_AZIMUTH = 315
    PLOT_ALTITUDE = 45

    def __init__(
        self,
        dem_path: str,
        model_name: Optional[str] = None,
        ela: int = 2850,
        m: float = 0.006,
        tolerance: float = 0.0001,
        plot: bool = True,
    ) -> None:
        """
        Class constructor for the GlacierFlowModel class.

        Parameters
        ----------
        dem_path : str
            Path to the file that holds the DEM.
        model_name: Optional[str]
            Name of the model, if not provided the name of the input dem file
            without extension is set.
        ela : int, default 2850
            The equilibrium-line altitude (ELA) marks the area or zone on
            a glacier where accumulation is balanced by ablation over a 1-year
            period.
        m : float, default 0.006
            Glacier mass balance gradient [m/m], the linear relationship
            between altitude and mass balance.
        tolerance : float, default 0.0001
            Tolerance to check if mass balance is constantly around zero and
            therefore a steady state is reached.
        plot : bool, default True
            Visualization of the simulation process.

        Returns
        -------
        None

        """

        # Load DEM ------------------------------------------------------------
        dem = Open(dem_path)
        band = dem.GetRasterBand(1)
        ele = band.ReadAsArray()

        # Instance variables --------------------------------------------------
        self.model_name = Path(dem_path).stem if model_name is None else model_name
        self.dem_path = dem_path
        self.tolerance = tolerance
        self.precision = (
            len(search("\\d+\\.(0*)", str(tolerance)).group(1)) + 1  # type: ignore
        )
        self._log_string = (
            "Simulating year %s (ELA: %.0f, "
            + f"mass balance long-term trend: %.{self.precision}f) ..."
        )

        # Mass balance parameters
        self.m = m  # Mass balance gradient
        self.ela_start = ela  # Equilibrium line altitude
        self._setup_params()  # Variable parameters (i, ela, steady_state)

        # 2D arrays
        self.ele_orig = np.array(ele)  # Original topography
        self._setup_arrays()  # Variable arrays (ele, h, u ,hs)

        # Coordinates
        self._geo_trans = dem.GetGeoTransform()
        self._geo_proj = dem.GetProjection()
        self.res = dem.GetGeoTransform()[1]  # Resolution
        nrows, ncols = ele.shape
        x0, dx, dxdy, y0, dydx, dy = dem.GetGeoTransform()
        x1 = x0 + dx * ncols
        y1 = y0 + dy * nrows
        self.extent = [x0, x1, y1, y0]  # Geographical extent of file

        # Define empty row and column for later F8 shift
        self.newcolumn = np.zeros((ele.shape[0], 1))
        self.newrow = np.zeros((1, ele.shape[1]))

        # Setup statistics
        self._setup_stats()

        # Setup plot
        self.plot = plot

    @property
    def plot(self) -> bool:
        LOG.debug("Access plot via getter method; masking value to boolean.")
        if self._fig is None:
            return False
        return True

    @plot.setter
    def plot(self, value: bool) -> None:
        if value:
            self._fig = self._setup_plot(self.PLOT_WIDTH, self.PLOT_HEIGHT)
            self._update_plot()
        else:
            self._destroy_plot()

    def _setup_params(self) -> None:
        """
        Setup model parameter

        Resets the non constant model parameters.

        Returns
        -------
        None

        """
        self.i = 0  # Year
        self.ela = self.ela_start  # Equilibrium line altitude
        self.steady_state = False  # Control variable for steady state

    def _setup_arrays(self) -> None:
        """
        Setup arrays

        Resets the model arrays internally.

        Returns
        -------
        None

        """
        # 2D arrays
        self.ele = self.ele_orig  # Elevation including glaciers
        self.h = self.ele_orig * 0  # Glacier geometry
        self.u = self.ele_orig * 0  # Glacier velocity
        self.hs = self._hillshade(
            self.ele_orig, self.PLOT_AZIMUTH, self.PLOT_ALTITUDE
        )  # HS

    def __del__(self) -> None:
        self._destroy_plot()

    def __repr__(self) -> str:
        return (
            "GlacierFlowModel("
            + f"{self.dem_path}, {self.model_name},"
            + f"{self.ela_start}, {self.m}, "
            + f"{self.tolerance}, {self.plot})"
        )

    def __str__(self) -> str:
        """
        Print method of the GlacierFlowModel class.

        Returns
        -------
        str
            Information about the model state and parameters.

        """
        return (
            f"GlacierFlowModel '{self.model_name}' "
            f"{'' if self.steady_state else 'not '}in steady state with:"
            f"\n - m:          {self.m:20.5f} [m/m]"
            f"\n - ela:        {self.ela:20.2f} [m MSL]"
            f"\n - resolution: {self.res:20.2f} [m]"
            f"\n - extent:           min        max"
            f"\n              {self.extent[0]:10.1f} "
            f"{self.extent[1]:10.1f} [x]"
            f"\n              {self.extent[2]:10.1f} "
            f"{self.extent[3]:10.1f} [y]"
        )

    def reach_steady_state(self, max_years: int = 10000) -> None:
        """
        Iterates the model until a steady state in the mass balance is
        reached.

        After initialization of the model needs to accumulate the initial ice
        mass. This is done by iterating through years, where every year
        contains two steps:

        - Add the local mass balance (accumulation and ablation).
        - Let the ice flow.

        This steps are repeated until the change in mass balance is
        constantly low (mass_balance_l_trend < tolerance, default 0.0001).

        Parameters
        ----------
        max_years : int, default 10000
            Maximum numbers of years to iterate until steady_state is
            reached.

        Returns
        -------
        None
            The model state changes internally.

        """
        # Reset year, state of model and stats
        self._setup_params()
        self._setup_arrays()
        self._setup_stats()

        # Reset plot if active
        if self._fig is not None:
            self.plot = True

        # Loop through years
        _ = self._iterate(temp_change=0, max_years=max_years)

    def simulate(self, temp_change: float, max_years: int = 10000) -> None:
        """
        Simulate a temperature change.

        After steady state of a model is reached (reach_steady_state()), a
        temperature change can be simulated. This method applies the
        temperature change (negative or positive) to the initially set
        parameters (ela) and iterates the model until a steady state is reached
        again (mass_balance_l_trend < tolerance, default 0.0001).

        Parameters
        ----------
        temp_change : float
            Negative or positive temperature change value in degrees [°].
        max_years : int, default 10000
            Maximum numbers of years to iterate until steady_state is reached.

        Returns
        -------
        None
            The model state changes internally.

        """

        # If steady state is not reached yet, exit the method
        if not self.steady_state:
            LOG.warning(
                "Model is not yet in steady state, "
                "call 'reach_steady_state()' method on the model object first."
            )
            return None

        # Reset year and state of model
        self.i = 0
        self.steady_state = False

        # Loop through years
        _ = self._iterate(temp_change=temp_change, max_years=max_years)

    def _iterate(self, temp_change: float, max_years: int) -> bool:

        # Iterate years until steady state or abort
        for i in range(max_years):
            LOG.info(self._log_string, i, self.ela, self.mass_balance_l_trend[-1])
            self.i = i
            self._add_mass_balance()
            self._flow()
            self._update_stats()
            if i % self.PLOT_FRAME_RATE == 0:
                self._update_plot()

            # Adjust temperature change
            if temp_change > 0 and self.ela < (self.ela_start + 100 * temp_change):
                self.ela += 1
            elif temp_change < 0 and self.ela > (self.ela_start + 100 * temp_change):
                self.ela -= 1

            # Check if mass balance is constantly around zero; steady state
            if -self.tolerance <= self.mass_balance_l_trend[-1] <= self.tolerance:
                self.steady_state = True
                LOG.info(
                    "Steady state reached after %s years (ELA: %s, dT = %s).",
                    self.i,
                    self.ela,
                    temp_change,
                )
                return True

        LOG.warning("Steady state was not reached after %s years.", max_years)
        return False

    def _add_mass_balance(self) -> None:
        """
        Add surface mass balance to the model.

        This method adds the surface mass balances (adds accumulation and
        subtracts ablation) to the raster cells of the model. The mass balance
        is calculated using the equilibrium-line altitude (ELA) and the glacier
        mass balance gradient [m/m].

        Returns
        -------
        None
            The model state changes internally.

        """
        # Add new accumulation / ablation on the layer ------------------------
        # Surface mass balance
        b = self.m * (self.ele_orig - self.ela)
        self.h += b  # type: ignore
        self.h = self.h * (self.h > 0)

        # Update elevation with new glacier geometry
        self.ele = self.ele_orig + self.h
        ele = gaussian_filter(self.ele, sigma=5)
        self.ele = self.ele_orig * (self.h == 0) + ele * (self.h > 0)

    def _flow(
        self, a: float = 1.4, f: float = 1, p: float = 918, g: float = 9.81
    ) -> None:
        """
        Simulates the flow of the ice for one year.

        The ice flow is modeled using the D8 flow direction technique
        to determine the direction of the flow and the velocity
        of the ice per raster cell to estimate the proportion of the ice
        that flows out of each cell. This proportion is then added to the
        neighbouring cell, which is in the direction of the flow.

        Parameters
        ----------
        a : float, default 1.4 * 10e-16
            The rate factor of ice.
        f : float, default 1
            Valley shape factor.
        p : float, default 918
            The mean density of the glacier ice [kg/m^3].
        g : float, default 9.81^
            Earth's acceleration [m/s^2].

        Returns
        -------
        None
            The model state changes internally.

        """
        # Aspect and slope ----------------------------------------------------
        # Calculate slope
        x_slp, y_slp = np.gradient(self.ele, 22, 22)
        slp = np.arctan(np.sqrt(x_slp * x_slp + y_slp * y_slp))

        # Calculate aspect
        x_asp, y_asp = np.gradient(self.ele, 3, 3)
        asp = np.arctan2(-y_asp, x_asp)
        asp[asp < 0] += 2 * np.pi

        # Classify aspect F8
        asp = np.round(((asp - np.radians(22.5)) / np.radians(40)), decimals=0)
        asp[asp == 0] = 8
        asp[asp == -1] = 7

        # Random nudging the flow
        if self.MODEL_RANDOM_NUDGING:
            asp = asp + np.clip(
                np.random.normal(loc=0.0, scale=1.0, size=asp.shape).astype(int), -1, 1
            )
            asp[asp == 9] = 1
            asp[asp == 0] = 8

        # Ice flow ------------------------------------------------------------
        # Calculate ice flow velocity 'u'
        ud = (2 * a * ((f * p * g * np.sin(slp)) ** 3.0) * self.h ** 4.0) / 4
        self.u = ud / 100
        self.u[self.u > 0.99 * self.res] = 0.99 * self.res

        # Change of ice per pixel that changes
        change = (self.u / self.res) * self.h

        # Calculate the flow per direction 'D8' -------------------------------
        change_1 = change * (asp == 8)
        change_1 = np.concatenate((change_1, self.newrow), axis=0)
        change_1 = np.delete(change_1, (0), axis=0)

        change_2 = change * (asp == 1)
        change_2 = np.concatenate((change_2, self.newrow), axis=0)
        change_2 = np.delete(change_2, (0), axis=0)
        change_2 = np.concatenate((self.newcolumn, change_2), axis=1)
        change_2 = np.delete(change_2, (-1), axis=1)

        change_3 = change * (asp == 2)
        change_3 = np.concatenate((self.newcolumn, change_3), axis=1)
        change_3 = np.delete(change_3, (-1), axis=1)

        change_4 = change * (asp == 3)
        change_4 = np.concatenate((self.newrow, change_4), axis=0)
        change_4 = np.delete(change_4, (-1), axis=0)
        change_4 = np.concatenate((self.newcolumn, change_4), axis=1)
        change_4 = np.delete(change_4, (-1), axis=1)

        change_5 = change * (asp == 4)
        change_5 = np.concatenate((self.newrow, change_5), axis=0)
        change_5 = np.delete(change_5, (-1), axis=0)

        change_6 = change * (asp == 5)
        change_6 = np.concatenate((self.newrow, change_6), axis=0)
        change_6 = np.delete(change_6, (-1), axis=0)
        change_6 = np.concatenate((change_6, self.newcolumn), axis=1)
        change_6 = np.delete(change_6, (0), axis=1)

        change_7 = change * (asp == 6)
        change_7 = np.concatenate((change_7, self.newcolumn), axis=1)
        change_7 = np.delete(change_7, (0), axis=1)

        change_8 = change * (asp == 7)
        change_8 = np.concatenate((change_8, self.newrow), axis=0)
        change_8 = np.delete(change_8, (0), axis=0)
        change_8 = np.concatenate((change_8, self.newcolumn), axis=1)
        change_8 = np.delete(change_8, (0), axis=1)

        # Calculate new glacier height 'h_new' after flow ---------------------
        self.h = (
            self.h
            - change
            + (
                change_1
                + change_2
                + change_3
                + change_4
                + change_5
                + change_6
                + change_7
                + change_8
            )
        )
        h_new_index = np.copy((self.h < self.m))
        self.h = uniform_filter(self.h, size=5)
        self.h[h_new_index] = 0

    # Export ------------------------------------------------------------------
    def export(self, folder_path: Optional[str] = None) -> None:
        """
        Export model data

        Export the glacier layer and statistics of the model as '.csv' and
        '.tif' into a new folder with the name of the model.

        Parameters
        ----------
        folder_path : Optional[str]
            Location to create a new folder and export the files.

        Returns
        -------
        None

        """
        if folder_path is None:
            folder_path = Path.cwd()
        else:
            folder_path = Path(folder_path)

        # Append model name and create folder
        folder_path = folder_path / self.model_name
        folder_path.mkdir(parents=True, exist_ok=True)

        # File names
        dst_csv = f"{self.model_name}_ela{self.ela}_m{self.m}.csv"
        dst_tif = f"{self.model_name}_ela{self.ela}_m{self.m}.tif"

        # Export
        self._export_csv(folder_path / dst_csv)
        self._export_tif(folder_path / dst_tif)

    def _export_csv(self, file_path: Path) -> None:
        header = "mass,mass_balance,mass_balance_s_trend,mass_balance_l_trend"
        statistics = np.asarray(
            np.c_[
                self.mass,
                self.mass_balance,
                self.mass_balance_s_trend,
                self.mass_balance_l_trend,
            ]
        )
        np.savetxt(
            file_path,
            statistics,
            delimiter=",",
            comments="",
            newline="\n",
            header=header,
        )

    def _export_tif(self, file_path: Path) -> None:
        driver = GetDriverByName("GTiff")
        data_set = driver.Create(
            str(file_path), self.h.shape[1], self.h.shape[0], 1, GDT_Float32
        )
        data_set.GetRasterBand(1).WriteArray(self.h)
        data_set.SetGeoTransform(self._geo_trans)
        data_set.SetProjection(self._geo_proj)
        data_set.FlushCache()

    # Statistics --------------------------------------------------------------
    def _setup_stats(self) -> None:
        """
        Setup statistics

        Resets the model statistics internally.

        Returns
        -------
        None

        """

        # Save statistics
        self.mass = np.array([0])
        self.mass_balance = np.array([0])
        self.mass_balance_s_trend = np.array([0])
        self.mass_balance_l_trend = np.array([0])

    def _update_stats(self) -> None:
        """
        Update statistics

        Updates the model statistics internally.

        Returns
        -------
        None

        """
        # Mass, only consider pixels with ice
        self.mass = np.append(self.mass, np.mean(self.h[self.h > 0]))

        # Difference mass 'mass balance'
        self.mass_balance = np.append(
            self.mass_balance, (self.mass[-1] - self.mass[-2])
        )

        # Calculate trend of mass balance (take last 20 and 100 elements)
        # Short term trend (20)
        if self.i < 20:
            self.mass_balance_s_trend = np.append(
                self.mass_balance_s_trend, np.mean(self.mass_balance)
            )
        else:
            self.mass_balance_s_trend = np.append(
                self.mass_balance_s_trend, np.mean(self.mass_balance[-20:])
            )
        # Long term trend (100)
        if self.i < 100:
            self.mass_balance_l_trend = np.append(
                self.mass_balance_l_trend, np.mean(self.mass_balance)
            )
        else:
            self.mass_balance_l_trend = np.append(
                self.mass_balance_l_trend, np.mean(self.mass_balance[-100:])
            )

    # Visualization -----------------------------------------------------------
    @staticmethod
    def _setup_plot(x: float, y: float) -> plt.figure:
        """
        Setup empty model plot

        Sets up an empty plot for the model. The plot can be updated with the
        current model state using the '_update_plot()' method.

        Parameters
        ----------
        x : float
            Width of the plot.
        y : float
            Height of the plot.

        Returns
        -------
        plt.figure
            An empty plot of the model.

        """
        LOG.debug("Initializing plot.")
        plt.ion()
        fig = plt.figure(figsize=(x, y), num="GlacierFlowModel")
        fig.patch.set_facecolor("black")
        return fig

    def _update_plot(self) -> None:
        """
        Update model plot

        Updates the plot of the model with the new ice layer.
        Call '_setup_plot()' first.

        Returns
        -------
        None

        """

        # Check if plotting is active
        if self._fig is None:
            return None
        LOG.debug("Updating plot.")

        # Extract glaciated area
        hs_back = np.ma.masked_where(
            self.h <= 1,
            self._hillshade(self.ele, self.PLOT_AZIMUTH, self.PLOT_ALTITUDE),
        )

        # Clear plot and draw axes
        self._fig.clear()
        ax = plt.subplot(121, facecolor="black")
        ax.tick_params(axis="x", colors="w")
        ax.tick_params(axis="y", colors="w")
        ax.set(xlabel="X-coordinate [m]", ylabel="Y-coordinate [m]")
        ax.xaxis.label.set_color("w")
        ax.yaxis.label.set_color("w")
        title_text = f"Year: {str(self.i)}  ELA: {str(int(self.ela))}"
        ax.set_title(title_text, color="white", size=20)

        # Draw new image layers
        plt.imshow(self.hs, vmin=90, vmax=345, cmap="copper", extent=self.extent)
        plt.imshow(255 - hs_back, vmin=1, vmax=150, cmap="Greys", extent=self.extent)

        # Mass balance
        ax1 = plt.subplot(222, facecolor="black")
        ax1.plot(self.mass_balance, color="w")
        ax1.plot(self.mass_balance_s_trend, color="r")
        ax1.set(ylabel="Mass balance [m]")
        ax1.yaxis.label.set_color("w")
        plt.setp(ax1.get_xticklabels(), visible=False)
        ax1.tick_params(axis="y", colors="w")

        # Plot mean thickness
        ax2 = plt.subplot(224, sharex=ax1, facecolor="black")
        ax2.plot(self.mass, color="w")
        ax2.set(xlabel="Year [a]", ylabel="Mean thickness [m]")
        ax2.xaxis.label.set_color("w")
        ax2.yaxis.label.set_color("w")
        ax2.tick_params(axis="x", colors="w")
        ax2.tick_params(axis="y", colors="w")

        # Draw new plot
        self._fig.canvas.draw()
        plt.pause(0.05)

    def _destroy_plot(self) -> None:
        """Destroy plot instance

        Returns
        -------
        None

        """
        try:
            plt.close(self._fig)
            LOG.debug("Destroying plot.")
        except AttributeError:
            pass
        self._fig = None

    @staticmethod
    def _hillshade(array: np.ndarray, azimuth: int, altitude: int) -> np.ndarray:
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
