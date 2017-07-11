###############################################################################
# Glacier Flow Model
# Authors:          Merlin Unterfinger, Manuel Luck
# Date:             11.07.2017
###############################################################################

import matplotlib as mpl
mpl.rcParams['toolbar'] = 'None'
import matplotlib.pyplot as plt
import numpy as np
from osgeo import gdal
import scipy.ndimage.filters as filter


class GlacierFlowModel(object):
    def __init__(self, DEM, ELA = 2850.0, m = 0.0006):
        # Load DEM ------------------------------------------------------------
        dem = gdal.Open(DEM)
        band = dem.GetRasterBand(1)
        ele = band.ReadAsArray()

        # Instance variables --------------------------------------------------
        # 2D arrays
        self.ele_orig = np.array(ele)  # Original topography
        self.ele = np.array(ele)  # Elevation including glaciers
        self.h = self.ele_orig * 0  # Glacier geometry
        self.u = self.ele_orig * 0  # Glacier velocity
        self.hs = self.hillshade(ele, azimuth=315, angle_altitude=45)  # HS

        # Mass balance parameters
        self.m = m  # Gradient
        self.ELA = ELA  # Equilibrium line altitude
        self.ELA_start = ELA  # Equilibrium line altitude
        self.i = 0  # Year
        self.steady_state = False  # Control variable for steady state

        # Geocode
        self.res = dem.GetGeoTransform()[1] # Resolution
        nrows, ncols = ele.shape
        x0, dx, dxdy, y0, dydx, dy = dem.GetGeoTransform()
        x1 = x0 + dx * ncols
        y1 = y0 + dy * nrows
        self.extent = [x0, x1, y1, y0]  # Geographical extent of file

        # Define empty row and column for later F8 Shift
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

    def reach_steady_state(self, years=10000):
        # Reset stats, year and state of model
        self.i = 0
        self.steady_state = False
        self.mass = np.array([0])
        self.mass_balance = np.array([0])
        self.mass_balance_s_trend = np.array([0])
        self.mass_balance_l_trend = np.array([0])

        # Loop through years
        for i in xrange(years):
            # print '----------Year: ', i, ' -----------'
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
                return ('Steady state reached after ' + str(self.i) +
                ' years (ELA: ' + str(self.ELA) + ').')

        # Set steady variable to True
        self.steady_state = True
        return "Steady State was not reached after 10'000 years"

    def simulate(self, temp_change, years=10000):
        if self.steady_state:
            # Reset year and state of model
            self.i = 0
            self.steady_state = False

            # Loop through years
            for i in xrange(years):
                # print '----------Year: ', i, ' -----------'
                self.i = i
                self.add_mass_balance()
                self.flow()
                self.update_stats()
                if i % 5 == 0:
                    self.update_plot()

                # Adjust temperature change
                if temp_change > 0:
                    if self.ELA < (self.ELA_start + 100 * temp_change):
                        self.ELA += 1
                elif temp_change < 0:
                    if self.ELA > (self.ELA_start + 100 * temp_change):
                        self.ELA -= 1

                # Check if mass balance is constantly around zero; steady state
                if -0.0001 <= self.mass_balance_l_trend[-1] <= 0.0001:
                    self.steady_state = True
                    return ('Steady state reached after ' + str(self.i) +
                    ' years (ELA: ' + str(self.ELA) + ', dT = ' +
                            str(temp_change)+ ').')

            return "Steady State was not reached after 10'000 years"

        # If steady state is not reached yet, exit the method
        else:
            return("Model is not yet in steady state. " +
                  "Please press 'Steady state' first.")

    def add_mass_balance(self):
        # Add new accumulation / ablation on the layer ------------------------
        # Surface mass balance
        b = self.m * (self.ele_orig - self.ELA)
        self.h += b
        self.h = self.h * (self.h > 0)

        # Update elevation with new glacier geometry
        self.ele = self.ele_orig + self.h
        ele = filter.gaussian_filter(self.ele, sigma=5)
        self.ele = self.ele_orig * (self.h == 0) + ele * (self.h > 0)

    def flow(self, A=1.4, f=1, p=918, g=9.81):
        """
        A = 1.4 * 10e-16  # Rate factor Ice
        f = 1  # Valley shape factor
        p = 918  # Density Kg/m3
        g = 9.81  # Earth's acceleration [m/s^2]
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
        #self.u[self.u > self.res] = self.res
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
        self.h = self.h - change + (change_1 + change_2 + change_3 + change_4
                                  + change_5 + change_6 + change_7 + change_8)

        h_new_index = np.copy((self.h < self.m))
        self.h = filter.uniform_filter(self.h, size=5)
        self.h[h_new_index] = 0

    def update_stats(self):
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
    def setup_plot(x=15, y=5):
        plt.ion()
        fig = plt.figure(figsize=(x, y))
        fig.patch.set_facecolor('black')
        return fig

    def update_plot(self):
        # Extract glaciated area
        hs_back = np.ma.masked_where(self.h <= 1,
                                     self.hillshade(self.ele,
                                                    azimuth=315,
                                                    angle_altitude=45))
        h = np.ma.masked_where(self.h <= 1, self.h)

        # Clear plot and draw axes
        self.fig.clear()
        ax = plt.subplot(121, axisbg='black')
        ax.tick_params(axis='x', colors='w')
        ax.tick_params(axis='y', colors='w')
        plt.xlabel('X-coordinate [m]')
        ax.xaxis.label.set_color('w')
        plt.ylabel('Y-coordinate [m]')
        ax.yaxis.label.set_color('w')
        title_text = 'Year: ' + str(self.i) + '   ELA: ' + str(int(self.ELA))
        ax.set_title(title_text, color='white', size=20)

        # Draw new image layers
        plt.imshow(self.hs, vmin=90, vmax=345, cmap='copper',
                   extent=self.extent)
        plt.imshow(255 - hs_back, vmin=1, vmax=150, cmap='Greys',
                   extent=self.extent)

        # Plot mean velocity
        ax1 = plt.subplot(222, axisbg='black')
        plt.plot(self.mass_balance, color='w')
        plt.plot(self.mass_balance_s_trend, color='r')
        plt.ylabel('Mass balance [m]')
        ax1.yaxis.label.set_color('w')
        plt.setp(ax1.get_xticklabels(), visible=False)
        ax1.tick_params(axis='y', colors='w')

        # Plot maximum thickness
        ax2 = plt.subplot(224, sharex=ax1, axisbg='black')
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
    def hillshade(array, azimuth, angle_altitude):
        """
        Function to render hillshade from a DEM input.
        :param array: Input DEM
        :param azimuth: Direction of the illumination source
        :param angle_altitude: altitude of illumination source
        :return:
        """
        x, y = np.gradient(array, 22, 22)
        slope = np.pi / 2. - np.arctan(np.sqrt(x * x + y * y))
        x, y = np.gradient(array, 3, 3)
        aspect = np.arctan2(-y, x)
        azimuthrad = azimuth * np.pi / 180.
        altituderad = angle_altitude * np.pi / 180.

        shaded = np.sin(altituderad) * np.sin(slope) \
                 + np.cos(altituderad) * np.cos(slope) \
                   * np.cos(azimuthrad - aspect)

        return 255 * (shaded + 1) / 2
