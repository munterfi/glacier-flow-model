###############################################################################
# Glacier Flow Model: Render Scenarios
# Authors:          Merlin Unterfinger, Manuel Luck
# Date:             09.07.2017
###############################################################################

# from Packages.gradient import slope
import matplotlib.pyplot as plt
import numpy as np
from os import path
from osgeo import gdal
import scipy.ndimage.filters as filter
import pandas as pd

###############################################################################
# Set Up
###############################################################################

# Set Up Scenario to render
scenario = 'Cooling10'
temp_change = 0
steps = 5
numy = 6000
save_plots = False

# Set Accumulation - Parameters
ELA = 2850.0                        # Equilibrium Line Altitude
m = 0.0006                          # Alpine Gradient [m/m]

# Set Iceflow - Parameters
A = 1.4 * 10e-16                    # Rate factor Ice
f = 1                               # Valley shape factor
p = 918                             # Density Kg/m3
g = 9.81                            # Earth's acceleration [m/s^2]

# Set Parameters for Aspect and Slope
df_value_slp = 22                   # Number of df-pixels for Slope
df_value_asp = 3                    # Number of df-pixels for Aspect

# Path of DEM
raster_path = 'data'
figures_path = 'figures'
dem_name = 'dhm25_Bern.tif'
#dem_file = path.join(raster_path, dem_name)
dem_file = '/Users/Merlin/Documents/Projekte/glacier-flow-model/data/DEM.tif'



###############################################################################
# Open and Prepare DEM
###############################################################################

dem = gdal.Open(dem_file)
res = dem.GetGeoTransform()[1]
band = dem.GetRasterBand(1)
ele = band.ReadAsArray()
ele_orig = np.array(ele)

# Define empty row and column for later F8 Shift
newcolumn = np.zeros((ele.shape[0], 1))
newrow = np.zeros((1, ele.shape[1]))


###############################################################################
# Initialize Start Situation: First Glaciers Mass Balance 'm1'
###############################################################################

# Initial Surface Mass Balance
b = m * (ele_orig - ELA)

# Glaciated Area
h_old = b * (b > 0)


###############################################################################
# Render Hillshade
###############################################################################

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

hs = hillshade(ele, azimuth=315, angle_altitude=45)

###############################################################################
# Geocode
###############################################################################

nrows, ncols = ele.shape
x0, dx, dxdy, y0, dydx, dy = dem.GetGeoTransform()
x1 = x0 + dx * ncols
y1 = y0 + dy * nrows

###############################################################################
# Set_up Variables
###############################################################################

mean_vel = list()
mean_thick = list()
max_thick = list()
ela_list = list()
t = 0
ELA_start = ELA


###############################################################################
# Simulation
###############################################################################

for i in xrange(numy):
    print '----------Year: ', i, ' -----------'

    # Aspect and Slope --------------------------------------------------------
    # Calculate Slope
    x_slp, y_slp = np.gradient(ele, df_value_slp, df_value_slp)
    slp = np.arctan(np.sqrt(x_slp * x_slp + y_slp * y_slp))

    # Calculate Aspect
    x_asp, y_asp = np.gradient(ele, df_value_asp, df_value_asp)
    asp = np.arctan2(-y_asp, x_asp)
    asp[asp < 0] += 2 * np.pi

    # Classify Aspect F8
    asp = np.round(((asp - np.radians(22.5)) / np.radians(40)), decimals=0)
    asp[asp == 0] = 8
    asp[asp == -1] = 7

    # Nudging the Flow
    asp + np.random.randint(-1, 2, size=asp.shape)
    asp[asp == 9] = 1
    asp[asp == 0] = 8

    # Ice Flow ----------------------------------------------------------------
    # Calculate Ice Flow Velocity
    ud = (2 * A * ((f * p * g * np.sin(slp)) ** 3.0) * h_old ** 4.0) / 4
    u = ud / 100
    u[u > res] = res
    u[u > 0.99*res] = 0.99*res
    u = u

    # Change of Ice per Pixel that changes
    change = (u / res) * h_old

    # Calculate the Flow per Direction 'F8' -----------------------------------
    change_1 = change * (asp == 8)
    change_1 = np.concatenate((change_1, newrow), axis=0)
    change_1 = np.delete(change_1, (0), axis=0)

    change_2 = change * (asp == 1)
    change_2 = np.concatenate((change_2, newrow), axis=0)
    change_2 = np.delete(change_2, (0), axis=0)
    change_2 = np.concatenate((newcolumn, change_2), axis=1)
    change_2 = np.delete(change_2, (-1), axis=1)

    change_3 = change * (asp == 2)
    change_3 = np.concatenate((newcolumn, change_3), axis=1)
    change_3 = np.delete(change_3, (-1), axis=1)

    change_4 = change * (asp == 3)
    change_4 = np.concatenate((newrow, change_4), axis=0)
    change_4 = np.delete(change_4, (-1), axis=0)
    change_4 = np.concatenate((newcolumn, change_4), axis=1)
    change_4 = np.delete(change_4, (-1), axis=1)

    change_5 = change * (asp == 4)
    change_5 = np.concatenate((newrow, change_5), axis=0)
    change_5 = np.delete(change_5, (-1), axis=0)

    change_6 = change * (asp == 5)
    change_6 = np.concatenate((newrow, change_6), axis=0)
    change_6 = np.delete(change_6, (-1), axis=0)
    change_6 = np.concatenate((change_6, newcolumn), axis=1)
    change_6 = np.delete(change_6, (0), axis=1)

    change_7 = change * (asp == 6)
    change_7 = np.concatenate((change_7, newcolumn), axis=1)
    change_7 = np.delete(change_7, (0), axis=1)

    change_8 = change * (asp == 7)
    change_8 = np.concatenate((change_8, newrow), axis=0)
    change_8 = np.delete(change_8, (0), axis=0)
    change_8 = np.concatenate((change_8, newcolumn), axis=1)
    change_8 = np.delete(change_8, (0), axis=1)

    # Calculate new Glacier Height Layer 'h_new' after Flow -------------------
    h_new = h_old - change + (change_1 + change_2 + change_3 + change_4
                              + change_5 + change_6 + change_7 + change_8)

    h_new_index = np.copy((h_new < m))
    h_new = filter.uniform_filter(h_new, size=5)
    h_new[h_new_index] = 0

    # Add new Accumulation / Ablation on the Layer ----------------------------
    # Surface Mass Balance
    b = m * (ele_orig - ELA)
    h_new += b
    h_old = h_new * (h_new > 0)

    # Update elevation with new Glacier Situation -----------------------------
    ele = ele_orig + h_old
    ele = filter.gaussian_filter(ele, sigma=5)
    ele = ele_orig * (h_old == 0) + ele * (h_old > 0)

    # Print stats for the current year ----------------------------------------
    mean_thick_val = round(np.mean(h_old[h_old > 0]), 2)
    mean_vel_val = round(np.mean(u[u > 0]), 2)
    max_thick_val = round(np.amax(h_old), 2)
    print 'Min/Max aspect: ', round(np.amin(asp), 0), round(np.amax(asp), 0)
    print 'Mean Velocity:  ', mean_vel_val, \
        ' (', round(np.amin(u[u > 0]), 2), round(np.amax(u), 2), ')'
    print 'Max Thickness:  ', max_thick_val
    print 'Mean Thickness: ', mean_thick_val
    print 'ELA:            ', ELA, '\n'
    mean_thick.append(mean_thick_val)
    max_thick.append(max_thick_val)
    mean_vel.append(mean_vel_val)
    ela_list.append(ELA)

    # Plot --------------------------------------------------------------------
    # Masking glaciers arrays
    if i % steps == 0:
        hs_back = np.ma.masked_where(h_old <= 1, hillshade(ele,
                                                           azimuth=315,
                                                           angle_altitude=45))
        h = np.ma.masked_where(h_old <= 1, h_old)

        if i == 0:
            plt.ion()
            # Setup plot
            #fig = plt.figure(figsize=(20, 15))
            fig = plt.figure()
            fig.patch.set_facecolor('black')

        # Plot images
        fig.clear()
        ax = plt.subplot(111, axisbg='black')
        ax.tick_params(axis='x', colors='w')
        ax.tick_params(axis='y', colors='w')
        plt.imshow(hs, vmin=90, vmax=345, cmap='copper',
                   extent=[x0, x1, y1, y0])
        plt.imshow(255 - hs_back, vmin=1, vmax=150, cmap='Greys',
                   extent=[x0, x1, y1, y0])

        titletext = 'Year: ' + str(i) + '   ELA: ' + str(int(ELA))
        ax.set_title(titletext, color='white', size=20)

        if save_plots:
            fig_name = scenario+'_'+str(t)+'.png'
            plt.savefig(path.join(figures_path, fig_name),
                        facecolor=fig.get_facecolor(), edgecolor='none')
            plt.close(fig)

        fig.canvas.draw()
        plt.pause(0.05)

        # Update image count
        t += 1

    if temp_change == 0:
        None
    elif temp_change > 0:
        if ELA < (ELA_start + 100 * temp_change):
            ELA += 1
    elif temp_change < 0:
        if ELA > (ELA_start + 100 * temp_change):
            ELA -= 1

print 'End of loop'

# # Save array
# np.savetxt(path.join(data_path, scenario+'.txt'), h_old)
# print 'Array saved.'
#
# # Save stats
# stats = pd.DataFrame([mean_thick, max_thick, mean_vel, ela_list])
# stats.to_csv(path.join(data_path, scenario+'.csv'), index=False, header=False, sep=';')
# print 'Stats saved.'
