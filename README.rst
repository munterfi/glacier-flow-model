.. image:: https://raw.githubusercontent.com/munterfinger/glacier-flow-model/develop/docs/source/_static/logo.svg
   :width: 120 px
   :alt: zeitsprung.fm
   :align: right

==========
zeitsprung
==========


.. image:: https://github.com/munterfinger/glacier-flow-model/workflows/test/badge.svg
        :target: https://github.com/munterfinger/glacier-flow-model/actions?query=workflow%3Atest

.. image:: https://readthedocs.org/projects/glacier-flow-model/badge/?version=latest
        :target: https://glacier-flow-model.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/munterfinger/glacier-flow-model/shield.svg
        :target: https://pyup.io/repos/github/munterfinger/glacier-flow-model/
        :alt: Updates

.. image:: https://codecov.io/gh/munterfinger/glacier-flow-model/branch/master/graph/badge.svg
        :target: https://codecov.io/gh/munterfinger/glacier-flow-model

==================
Glacier Flow Model
==================

Modeling glaciers flow, grounded on the glaciers mass balance and a digital elevation model (DEM).

The modeling is based on a linear relationship between altitude and mass balance, called the gradient.
For alpine glaciers this gradient is around 0.006m/m. Continental glaciers are
more around 0.003 and maritime glaciers 0.01m/m. The alpine gradient is set by default.
To model the glaciers flow, yearly steps are calculated. First the mass balance
for the area is added to the glacial layer and in a next step to flow is simulated
by applying the D8 technique, which is well-known for modeling water flows over terrain.
To avoid pure convergence of the flow a random nudging of the flow is added. Afterwards
the surface is smoothed slightly and plotted to the screen. The simulation stops
if the difference observed in the mass balance for a smoothed curve (n=-100)
is below 0.0001m

Data
----

The example DEM provided in this package is from [swisstopo](https://www.swisstopo.admin.ch/en/home.html) and
can be [downloaded](https://shop.swisstopo.admin.ch/en/products/height_models/dhm25200) for free.
It covers the area of Switzerland and has a resolution of 200m. In order to speed up
the calculations, the DEM provided here was cut to a smaller extent around the Aletsch glacial arena.
But the simulation can also be run on the original file of swisstopo, just follow
the download link above, unzip the directory and open the :code:`DHM200.asc` file with the glacier flow model.

Usage
-----

To use the GlacierFlowModel, first a DEM in the GeoTiff (or .asc)
file format has to be specified. Keep the input file size small, otherwise
the program may be slowed down remarkably. Then hit the :code:`Load dem` button to open the DEM.
Afterwards the model needs to accumulate the initial ice mass with the mass
balance parameters for the year 2000, which are set by default.
The first steady state of the model is calculated by hitting the :code:`Steady state` button.

|![Screen01](docs/source/_static/Screen01.png) | ![Screen02](docs/source/_static/Screen02.png)|
|---|---|

After reaching steady state a change in temperature can be simulated. Simply use
the slider to choose the temperature change and press :code:`Simulation`,
to simulate the further development of the glaciers.

Heating 4.5°C after steady state:

|![Screen03](docs/source/_static/Screen03.png ) | ![Screen04](docs/source/_static/Screen04.png)|
|---|---|

Cooling -1°C after steady state:

|![Screen05](docs/source/_static/Screen05.png ) | ![Screen06](docs/source/_static/Screen06.png)|
|---|---|

License
-------

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
