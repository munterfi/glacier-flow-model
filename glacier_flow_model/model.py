import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from osgeo.gdal import Open
from scipy.ndimage.filters import gaussian_filter, uniform_filter
from glacier_flow_model.base import Base

# Disable toolbar
mpl.rcParams['toolbar'] = 'None'


class GlacierFlowModel(Base):
    """Class for modeling glacier flow."""

    def __init__(self, dem_path: str, ela: int = 2850, m: float = 0.0006,
                 verbose: bool = True) -> None:
        """
        Class constructor for the GlacierFlowModel class.

        Parameters
        ----------
        dem_path : str
            Path to the file that holds the DEM.
        ela : int, default 2850
            The equilibrium-line altitude (ELA) marks the area or zone on
            a glacier where accumulation is balanced by ablation over a 1-year
            period.
        m : float, default 0.0006
            Glacier mass balance gradient [m/m], the linear relationship
            between altitude and mass balance.
        verbose : bool, default True
            Print messages about the activities of the class instance.

        Returns
        -------
        None

        """

        # Load DEM ------------------------------------------------------------
        dem = Open(dem_path)
        band = dem.GetRasterBand(1)
        ele = band.ReadAsArray()

        # Instance variables --------------------------------------------------
        super().__init__(verbose)
        self.verbose = verbose

        # 2D arrays
        self.ele_orig = np.array(ele)   # Original topography
        self.ele = np.array(ele)        # Elevation including glaciers
        self.h = self.ele_orig * 0      # Glacier geometry
        self.u = self.ele_orig * 0      # Glacier velocity
        self.hs = self.hillshade(ele, azimuth=315, angle_altitude=45)  # HS

        # Mass balance parameters
        self.m = m                      # Gradient
        self.ela = ela                  # Equilibrium line altitude
        self.ela_start = ela            # Equilibrium line altitude
        self.i = 0                      # Year
        self.steady_state = False       # Control variable for steady state

        # Geo coordinates
        self.res = dem.GetGeoTransform()[1]  # Resolution
        nrows, ncols = ele.shape
        x0, dx, dxdy, y0, dydx, dy = dem.GetGeoTransform()
        x1 = x0 + dx * ncols
        y1 = y0 + dy * nrows
        self.extent = [x0, x1, y1, y0]  # Geographical extent of file

        # Define empty row and column for later F8 shift
        self.newcolumn = np.zeros((ele.shape[0], 1))
        self.newrow = np.zeros((1, ele.shape[1]))

        # Save statistics
        self.mass = np.array([0])
        self.mass_balance = np.array([0])
        self.mass_balance_s_trend = np.array([0])
        self.mass_balance_l_trend = np.array([0])

        # Setup plot ----------------------------------------------------------
        self.fig = self.setup_plot()
        self.update_plot()

    def __str__(self) -> str:
        """
        Print method of the GlacierFlowModel class.

        Returns
        -------
        str
            Information about the model state and parameters.

        """
        return f"GlacierFlowModel {'' if self.steady_state else 'not '}" \
               f"in steady state with:" \
               f"\n - m:          {self.m:20.5f} [m/m]" \
               f"\n - ela:        {self.ela:20.2f} [m MSL]" \
               f"\n - resolution: {self.res:20.2f} [m]" \
               f"\n - extent:           min        max" \
               f"\n              {self.extent[0]:10.1f} " \
               f"{self.extent[1]:10.1f} [x]" \
               f"\n              {self.extent[2]:10.1f} " \
               f"{self.extent[3]:10.1f} [y]"

    def reach_steady_state(self, max_years: int = 10000) -> str:
        """
        Iterates the model until a steady state in the mass balance is
        reached.

        After initialization of the model needs to accumulate the initial ice
        mass. This is done by iterating through years, where every year
        contains two steps:

         - Add the local mass balance (accumulation and ablation).
         - Let the ice flow.

         This steps are repeated until the change in mass balance is
         constantly low (dm_trend < 0.0001).

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
        # Reset stats, year and state of model
        self.i = 0
        self.steady_state = False
        self.mass = np.array([0])
        self.mass_balance = np.array([0])
        self.mass_balance_s_trend = np.array([0])
        self.mass_balance_l_trend = np.array([0])

        # Loop through years
        for i in range(max_years):
            self.i = i
            self.add_mass_balance()
            self.flow()
            self.update_stats()
            if i % 5 == 0:
                self.update_plot()

            # Check if mass balance is constantly around zero; steady state
            if -0.0001 <= self.mass_balance_l_trend[-1] <= 0.0001:
                # Set steady variable to True
                self.steady_state = True
                return f'Steady state reached after {self.i} ' \
                       f'years (ELA: {self.ela}).'

        # Set steady variable to True
        self.steady_state = True
        return "Steady State was not reached after 10'000 years"

    def simulate(self, temp_change: float, max_years: int = 10000) -> str:
        """
        Simulate a temperature change.

        After steady state of a model is reached (reach_steady_state()), a
        temperature change can be simulated. This method applies the
        temperature change (negative or positive) to the initially set
        parameters (ela) and iterates the model until a steady state is reached
        again.

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
        if self.steady_state:
            # Reset year and state of model
            self.i = 0
            self.steady_state = False

            # Loop through years
            for i in range(max_years):
                # print '----------Year: ', i, ' -----------'
                self.i = i
                self.add_mass_balance()
                self.flow()
                self.update_stats()
                if i % 5 == 0:
                    self.update_plot()

                # Adjust temperature change
                if temp_change > 0:
                    if self.ela < (self.ela_start + 100 * temp_change):
                        self.ela += 1
                elif temp_change < 0:
                    if self.ela > (self.ela_start + 100 * temp_change):
                        self.ela -= 1

                # Check if mass balance is constantly around zero; steady state
                if -0.0001 <= self.mass_balance_l_trend[-1] <= 0.0001:
                    self.steady_state = True
                    return f'Steady state reached after {self.i} ' \
                           f'years (ELA: {self.ela}, dT = {temp_change})'

            return "Steady State was not reached after 10'000 years"

        # If steady state is not reached yet, exit the method
        else:
            return "Model is not yet in steady state. " \
                   "Please press 'Steady state' first."

    def add_mass_balance(self) -> None:
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
        self.h += b
        self.h = self.h * (self.h > 0)

        # Update elevation with new glacier geometry
        self.ele = self.ele_orig + self.h
        ele = gaussian_filter(self.ele, sigma=5)
        self.ele = self.ele_orig * (self.h == 0) + ele * (self.h > 0)

    def flow(self, A: float = 1.4, f: float = 1, p: float = 918,
             g: float = 9.81) -> None:
        """
        Simulates the flow of the ice for one year.

        The ice flow is modeled using the D8 flow direction technique
        to determine the direction of the flow and the velocity
        of the ice per raster cell to estimate the proportion of the ice
        that flows out of each cell. This proportion is then added to the
        neighbouring cell, which is in the direction of the flow.

        Parameters
        ----------
        A : float, default 1.4 * 10e-16
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

        # Nudging the flow
        asp + np.random.randint(-1, 2, size=asp.shape)
        asp[asp == 9] = 1
        asp[asp == 0] = 8

        # Ice flow ------------------------------------------------------------
        # Calculate ice flow velocity 'u'
        ud = (2 * A * ((f * p * g * np.sin(slp)) ** 3.0) * self.h ** 4.0) / 4
        self.u = ud / 100
        # self.u[self.u > self.res] = self.res
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
        self.h = self.h - change + (change_1 + change_2 + change_3 + change_4 +
                                    change_5 + change_6 + change_7 + change_8)

        h_new_index = np.copy((self.h < self.m))
        self.h = uniform_filter(self.h, size=5)
        self.h[h_new_index] = 0

    def update_stats(self) -> None:
        """
        Update statistics

        Updates the model statistics internally.

        Returns
        -------
        None
            Updates the model statistics internally.

        """
        # Mass, only consider pixels with ice
        self.mass = np.append(self.mass, np.mean(self.h[self.h > 0]))

        # Difference mass 'mass balance'
        self.mass_balance = np.append(self.mass_balance,
                                      (self.mass[-1] -
                                       self.mass[-2]))

        # Calculate trend of mass balance (take last 20 and 100 elements)
        # Short term trend (20)
        if self.i < 20:
            self.mass_balance_s_trend = np.append(self.mass_balance_s_trend,
                                                  np.mean(self.mass_balance))
        else:
            self.mass_balance_s_trend = np.append(
                self.mass_balance_s_trend, np.mean(self.mass_balance[-20:]))
        # Long term trend (100)
        if self.i < 100:
            self.mass_balance_l_trend = np.append(self.mass_balance_l_trend,
                                                  np.mean(self.mass_balance))
        else:
            self.mass_balance_l_trend = np.append(
                self.mass_balance_l_trend, np.mean(self.mass_balance[-100:]))

    @staticmethod
    def setup_plot(x: float = 15, y: float = 5) -> plt.figure:
        """
        Setup empty model plot

        Sets up an empty plot for the model. The plot can be updated with the
        current model state using the 'update_plot()' method.

        Parameters
        ----------
        x : float, default 15
            Width of the plot.
        y : float, default 5
            Height of the plot.

        Returns
        -------
        plt.figure
            An empty plot of the model.

        """
        plt.ion()
        fig = plt.figure(figsize=(x, y), num='GlacierFlowModel')
        fig.patch.set_facecolor('black')
        return fig

    def update_plot(self) -> None:
        """
        Update model plot

        Updates the plot of the model with the new ice layer.
        Call 'setup_plot()' first.

        Returns
        -------
        None

        """
        # Extract glaciated area
        hs_back = np.ma.masked_where(self.h <= 1,
                                     self.hillshade(self.ele,
                                                    azimuth=315,
                                                    angle_altitude=45))
        # h = np.ma.masked_where(self.h <= 1, self.h)

        # Clear plot and draw axes
        self.fig.clear()
        ax = plt.subplot(121, facecolor='black')
        ax.tick_params(axis='x', colors='w')
        ax.tick_params(axis='y', colors='w')
        plt.xlabel('X-coordinate [m]')
        ax.xaxis.label.set_color('w')
        plt.ylabel('Y-coordinate [m]')
        ax.yaxis.label.set_color('w')
        title_text = f'Year: {str(self.i)}  ELA: {str(int(self.ela))}'
        ax.set_title(title_text, color='white', size=20)

        # Draw new image layers
        plt.imshow(self.hs, vmin=90, vmax=345, cmap='copper',
                   extent=self.extent)
        plt.imshow(255 - hs_back, vmin=1, vmax=150, cmap='Greys',
                   extent=self.extent)

        # Plot mean velocity
        ax1 = plt.subplot(222, facecolor='black')
        plt.plot(self.mass_balance, color='w')
        plt.plot(self.mass_balance_s_trend, color='r')
        plt.ylabel('Mass balance [m]')
        ax1.yaxis.label.set_color('w')
        plt.setp(ax1.get_xticklabels(), visible=False)
        ax1.tick_params(axis='y', colors='w')

        # Plot maximum thickness
        ax2 = plt.subplot(224, sharex=ax1, facecolor='black')
        plt.plot(self.mass, color='w')
        plt.xlabel('Year [a]')
        ax2.xaxis.label.set_color('w')
        plt.ylabel('Mean thickness [m]')
        ax2.yaxis.label.set_color('w')
        ax2.tick_params(axis='x', colors='w')
        ax2.tick_params(axis='y', colors='w')

        # Draw new plot
        self.fig.canvas.draw()
        plt.pause(0.05)

    @staticmethod
    def hillshade(array: np.ndarray, azimuth: int,
                  angle_altitude: int) -> np.ndarray:
        """
        Render hillshade

        Calculates a shaded relief from a digital elevation model (DEM) input.

        Parameters
        ----------
        array : np.ndarray
            Digital elevation model.
        azimuth : int
            Direction of the illumination source.
        angle_altitude : int
            Altitude of illumination source

        Returns
        -------
        np.ndarray
            The rendered hillshade.

        """
        x, y = np.gradient(array, 22, 22)
        slope = np.pi / 2. - np.arctan(np.sqrt(x * x + y * y))
        x, y = np.gradient(array, 3, 3)
        aspect = np.arctan2(-y, x)
        azimuth_rad = azimuth * np.pi / 180.
        altitude_rad = angle_altitude * np.pi / 180.

        shaded = np.sin(altitude_rad) * np.sin(slope) + \
            np.cos(altitude_rad) * np.cos(slope) *\
            np.cos(azimuth_rad - aspect)

        return 255 * (shaded + 1) / 2
