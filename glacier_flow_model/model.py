"""The glacier flow model and visualization."""
from logging import getLogger
from pathlib import Path
from re import search
from typing import Optional

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from rasterio import open
from scipy.ndimage import gaussian_filter
from scipy.ndimage import uniform_filter

from .fracd8.flow import fracd8
from .utils.hillshade import hillshade
from .utils.store import ArrayStore

LOG = getLogger(__name__)

# Disable toolbar
mpl.rcParams["toolbar"] = "None"


class GlacierFlowModel:
    """
    Class for modeling glacier flow.

    Attributes
    ----------
    MODEL_TOLERANCE : float
        The fluctuation tolerance for the long-term trend of the mass balance
        to achieve a steady state of the model.
    MODEL_TREND_SIZE : int
        Number of iterations to average for the calculation of the mass balance
        trend. Defines also the minimum number of iterations to simulate after
        calling 'reach_steady_state' or 'simulate'.
    MODEL_RECORD_SIZE : int
        Number of iterations to keep record of the ndarrays in the ArrayStore
        (h and u) for the export.
    MODEL_FRACD8_OFFSET : int
        Maximum number of steps to follow the flow in cells with u > res. Since
        this is an experimental feature the default value is set to 0, which
        always chooses the limited version of fracd8, by default 0.
    FLOW_ICE_RATE_FACTOR : float
        The rate factor describes the deformability of the ice (default is
        tempered ice; 0°C: 1.4e-16, -5°C: 0.4e-16, -10°C: 0.05e-16).
    FLOW_ICE_DENSITY : float
        The density of the ice. It is assumed to be identical throughout the
        vertical column.
    FLOW_VALLEY_SHAPE_FACTOR : float
        Shape factor of the valleys between 0 and 1 in the model area (0:
        Infinitely narrow glacier, 0.5: Glacier with width equal to height,
        1.0: Infinitely wide glacier).
    FLOW_EARTH_ACCELERATION : float
        The gravity acceleration near the surface of the earth.
    PLOT_FRAME_RATE : int
        Rate of updating the plot in model years.
    PLOT_FIGURE_WIDTH : int
        Width of the plot figure.
    PLOT_FLIGURE_HEIGHT : int
        Height of the plot figure.
    PLOT_HILLSHADE_AZIMUTH : int
        Azimuth angle between 0 and 360 degrees of the light source for the
        hillshade calculation.
    PLOT_HILLSHADE_ALTITUDE : int
        Altitude angle between 0 and 90 degrees of the light source for the
        hillshade calculation.
    """

    MODEL_TOLERANCE = 0.0001
    MODEL_TREND_SIZE = 100
    MODEL_RECORD_SIZE = 10
    MODEL_FRACD8_OFFSET = 0

    FLOW_ICE_RATE_FACTOR = 1.4e-16
    FLOW_ICE_DENSITY = 917.0
    FLOW_VALLEY_SHAPE_FACTOR = 0.8
    FLOW_EARTH_ACCELERATION = 9.81

    PLOT_FRAME_RATE = 5
    PLOT_FIGURE_WIDTH = 15
    PLOT_FIGURE_HEIGHT = 5
    PLOT_HILLSHADE_AZIMUTH = 315
    PLOT_HILLSHADE_ALTITUDE = 45

    def __init__(
        self,
        dem_path: str,
        model_name: Optional[str] = None,
        ela: int = 2850,
        m: float = 0.006,
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
        plot : bool, default True
            Visualization of the simulation process.

        Returns
        -------
        None

        """

        # Load DEM ------------------------------------------------------------
        dem = open(dem_path)
        ele = dem.read(1).astype(np.float32)

        # Instance variables --------------------------------------------------
        self.model_name = Path(dem_path).stem if model_name is None else model_name
        self.dem_path = dem_path

        # Mass balance parameters
        self.m = m  # Mass balance gradient
        self.ela_start = ela  # Equilibrium line altitude
        self._setup_params()  # Variable parameters (i, ela, steady_state)

        # 2D arrays
        self.ele_orig = np.copy(ele)  # Original topography
        self._setup_ndarrays()  # Variable arrays (ele, h, u ,hs)

        # Coordinate reference system and dem resolution
        self._dem_meta = dem.meta
        self.res = dem.res[0]

        # Geographical extent of the dem
        x0, y0, x1, y1 = dem.bounds
        self.extent = (x0, x1, y1, y0)

        # Setup statistics
        self._setup_stats()

        # Setup plot
        self.plot = plot

    @property
    def precision(self) -> int:
        p = len(
            search("\\d+\\.(0*)", str(self.MODEL_TOLERANCE)).group(1)  # type: ignore
        )
        return p + 1

    @property
    def plot(self) -> bool:
        LOG.debug("Access plot via getter method; masking value to boolean.")
        if self._fig is None:
            return False
        return True

    @plot.setter
    def plot(self, value: bool) -> None:
        if value:
            self._fig = self._setup_plot(
                self.PLOT_FIGURE_WIDTH, self.PLOT_FIGURE_HEIGHT
            )
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
        self.fracd8_mode = "limited"  # Mode of the fracd8 algorithm

    def _setup_ndarrays(self) -> None:
        """
        Setup 2D arrays

        Resets the model arrays internally.

        Returns
        -------
        None

        """
        empty = self.ele_orig * 0
        # 2D arrays
        self.ele = np.copy(self.ele_orig)  # Elevation including glaciers
        self.slp = np.copy(empty)  # Slope with glacier geometry
        self.asp = np.copy(empty)  # Classified aspect with glacier geometry
        self.h = np.copy(empty)  # Local glacier height
        self.u = np.copy(empty)  # Local glacier velocity
        self.hs = hillshade(
            self.ele_orig,
            self.PLOT_HILLSHADE_AZIMUTH,
            self.PLOT_HILLSHADE_ALTITUDE,
        )  # HS

        # Initialize array store
        self.store = ArrayStore()
        self.store.create("h", self.MODEL_RECORD_SIZE)
        self.store.create("u", self.MODEL_RECORD_SIZE)

    def __del__(self) -> None:
        self._destroy_plot()

    def __repr__(self) -> str:
        return (
            "GlacierFlowModel("
            + f"dem_path={self.dem_path!r}, model_name={self.model_name!r}, "
            + f"ela={self.ela_start}, m={self.m}, "
            + f"plot={self.plot})"
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
        constantly low (mass_balance_trend < tolerance, default 0.0001).

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
        self._setup_ndarrays()
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
        again (mass_balance_trend < tolerance, default 0.0001).

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

        # Format logs
        log_template = (
            "Simulating year %s (ELA: %.0f, "
            + f"mass balance trend: %.{self.precision}f, fracd8: %s) ..."
        )

        # Iterate years until steady state or abort
        for i in range(max_years):
            LOG.info(
                log_template,
                i,
                self.ela,
                self.mass_balance_trend[-1],
                self.fracd8_mode,
            )
            self.i = i
            self._add_mass_balance()
            self._flow(
                a=self.FLOW_ICE_RATE_FACTOR,
                f=self.FLOW_VALLEY_SHAPE_FACTOR,
                p=self.FLOW_ICE_DENSITY,
                g=self.FLOW_EARTH_ACCELERATION,
            )
            self._update_stats()
            if i % self.PLOT_FRAME_RATE == 0:
                self._update_plot()

            # Add layers to array store
            self.store["h"] = self.h
            self.store["u"] = self.u

            # Adjust temperature change
            if temp_change > 0 and self.ela < (self.ela_start + 100 * temp_change):
                self.ela += 1
            elif temp_change < 0 and self.ela > (self.ela_start + 100 * temp_change):
                self.ela -= 1

            # Check if mass balance is constantly around zero; steady state
            if (self.i >= self.MODEL_TREND_SIZE) and (
                -self.MODEL_TOLERANCE
                <= self.mass_balance_trend[-1]
                <= self.MODEL_TOLERANCE
            ):
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
        ele = gaussian_filter(self.ele, sigma=3)
        self.ele = self.ele_orig * (self.h == 0) + ele * (self.h > 0)

    def _flow(
        self, a: float = 1.4 * 10e-16, f: float = 1, p: float = 918, g: float = 9.81
    ) -> None:
        """
        Simulates the flow of the ice for one year.

        The ice flow is modeled using the fracd8 flow direction technique
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
        self.slp = np.arctan(np.sqrt(x_slp * x_slp + y_slp * y_slp))

        # Ice flow ------------------------------------------------------------
        # u = ud + ub + us
        #   = ice deformation/creep + basal slide + soft bed deformation

        # Calculate ice deformation velocity 'ud' at glacier surface
        ud = (2 * a * ((f * p * g * np.sin(self.slp)) ** 3.0) * self.h**4.0) / 4

        # Assume linear decrease of 'ud' towards zero at the glacier bed use
        # velocity at medium height. Set u = ud, 'ub' and 'us' are ignored.
        ud = ud * 0.5

        # Limit maximum flow velocity to maxium fracd8 offset
        u_max = self.res * (self.MODEL_FRACD8_OFFSET + 1)
        ud[ud >= u_max] = u_max
        self.u = ud

        # Use limited or infnite 'fracd8' algorithm to simulate flow
        h_new, self.asp, self.fracd8_mode = fracd8(
            self.ele, self.u, self.h, self.res, self.MODEL_FRACD8_OFFSET
        )

        # Calculate new glacier height 'h_new' after flow ---------------------
        self.h = h_new
        h_new_index = np.copy((self.h < self.m))
        self.h = uniform_filter(self.h, size=5)
        self.h[h_new_index] = 0

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
        self.mass_balance_trend = np.array([0])

    def _update_stats(self) -> None:
        """
        Update statistics

        Updates the model statistics internally.

        Returns
        -------
        None

        """
        # Mass (average height in m), only consider pixels with ice
        self.mass = np.append(self.mass, np.mean(self.h[self.h > 0]))

        # Difference in mass 'mass balance'
        self.mass_balance = np.append(
            self.mass_balance, (self.mass[-1] - self.mass[-2])
        )

        # Calculate trend of mass balance (take last MODEL_TREND_SIZE elements)
        self.mass_balance_trend = np.append(
            self.mass_balance_trend,
            np.mean(self.mass_balance[-self.MODEL_TREND_SIZE :]),  # noqa: E203
        )

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
            export_folder_path = Path.cwd()
        else:
            export_folder_path = Path(folder_path)

        # Append model name and create folder
        export_folder_path = export_folder_path / self.model_name
        export_folder_path.mkdir(parents=True, exist_ok=True)

        # File names
        dst_csv = f"{self.model_name}_ela{self.ela}_m{self.m}.csv"
        dst_tif = f"{self.model_name}_ela{self.ela}_m{self.m}.tif"

        # Write files
        LOG.info(
            "Exporting files '%s' and '%s' to '%s'.",
            dst_csv,
            dst_tif,
            export_folder_path,
        )
        self._export_csv(export_folder_path / dst_csv)
        self._export_tif(export_folder_path / dst_tif)

    def _export_csv(self, file_path: Path) -> None:
        LOG.debug("Writing %i lines to '%s' ...", self.mass.shape[0], file_path)
        header = "mass,mass_balance,mass_balance_trend"
        statistics = np.asarray(
            np.c_[
                self.mass,
                self.mass_balance,
                self.mass_balance_trend,
            ]
        )
        np.savetxt(
            file_path,
            statistics,
            delimiter=",",
            comments="",
            newline="\n",
            fmt=f"%.{self.precision}f",
            header=header,
        )

    def _export_tif(self, file_path: Path) -> None:
        LOG.debug(
            "Writing (%ix%i) array to '%s' ...",
            self.h.shape[0],
            self.h.shape[1],
            file_path,
        )
        self._dem_meta.update(count=3)
        with open(file_path, "w", **self._dem_meta) as dst:
            dst.write_band(1, self.store.mean("h"))
            dst.write_band(2, self.store.mean("u"))
            dst.write_band(3, self.store.diff("h"))

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
            hillshade(
                self.ele, self.PLOT_HILLSHADE_AZIMUTH, self.PLOT_HILLSHADE_ALTITUDE
            ),
        )

        # Clear plot and draw axes
        self._fig.clear()
        ax = plt.subplot(121, facecolor="black")
        ax.tick_params(axis="x", colors="w")
        ax.tick_params(axis="y", colors="w")
        ax.set(xlabel="X-coordinate [m]", ylabel="Y-coordinate [m]")
        ax.xaxis.label.set_color("w")
        ax.yaxis.label.set_color("w")
        title_text = f"Year: {str(self.i)}  ELA: {str(int(self.ela))} m.a.s.l."
        ax.set_title(title_text, color="white", size=18)

        # Draw new image layers
        plt.imshow(self.hs, vmin=90, vmax=345, cmap="copper", extent=self.extent)
        plt.imshow(255 - hs_back, vmin=1, vmax=150, cmap="Greys", extent=self.extent)

        # Mass balance
        ax1 = plt.subplot(222, facecolor="black")
        ax1.plot(self.mass_balance, color="w")
        ax1.plot(self.mass_balance_trend, color="r")
        ax1.set(ylabel="Mass balance [m]")
        ax1.yaxis.label.set_color("w")
        plt.setp(ax1.get_xticklabels(), visible=False)
        ax1.tick_params(axis="y", colors="w")
        ax1.set_title(f"Gradient: {str(self.m)} m/m", color="white", size=18)

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
