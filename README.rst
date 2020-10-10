.. image:: https://raw.githubusercontent.com/munterfinger/glacier-flow-model/develop/docs/source/_static/logo.svg
   :width: 120 px
   :alt: https://github.com/munterfinger/glacier-flow-model
   :align: right

==================
Glacier flow model
==================

.. image:: https://github.com/munterfinger/glacier-flow-model/workflows/test/badge.svg
        :target: https://github.com/munterfinger/glacier-flow-model/actions?query=workflow%3Atest

.. image:: https://readthedocs.org/projects/glacier-flow-model/badge/?version=latest
        :target: https://glacier-flow-model.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://codecov.io/gh/munterfinger/glacier-flow-model/branch/master/graph/badge.svg
        :target: https://codecov.io/gh/munterfinger/glacier-flow-model

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

Installation
------------

The **glacier-flow-model** package depends on GDAL, which needs to be installed on the system.

macOS (using homebrew):

.. code-block:: shell

    brew install gdal

Linux (using aptitude):

.. code-block:: shell

    apt-get install gdal-bin libgdal-dev

Install the stable release of **glacier-flow-model** from pypi:

.. code-block:: shell

    pip install glacier-flow-model

Install the development version from `Github <https://github.com/munterfinger/glacier-flow-model>`_:

.. code-block:: shell

    git clone git://github.com/munterfinger/glacier-flow-model.git
    cd glacier-flow-model
    poetry install && poetry build
    python3 -m pip install dist/*

Data
----

The example DEM provided in this package is from `swisstopo <https://www.swisstopo.admin.ch/en/home.html>`_ and
can be downloaded `here <https://shop.swisstopo.admin.ch/en/products/height_models/dhm25200>`_.
It covers the area of Switzerland and has a resolution of 200m. In order to speed up
the calculations, the DEM provided here was cut to a smaller extent around the Aletsch glacial arena.
But the simulation can also be run on the original file of swisstopo, just follow
the download link above, unzip the directory and open the :code:`DHM200.asc` file with the glacier flow model.

Usage
-----

To set up a glacier flow model, a DEM in the GeoTiff (or .asc)
file format has to passed to the model class constructor. Keep the input file size small, otherwise
the model may be slowed down remarkably:

.. code-block:: python

    from glacier_flow_model import GlacierFlowModel
    gfm = GlacierFlowModel('data/dem.tif')

After initialization, the model needs to accumulate the initial ice mass until it reaches a steady state.
By default the mass balance parameters for the year 2000 are set. Calling the :code:`reach_steady_state`
method to do so:

.. code-block:: python

    gfm.reach_steady_state()

.. image:: https://raw.githubusercontent.com/munterfinger/glacier-flow-model/develop/docs/source/_static/steady_state_initial.png
   :width: 120 px
   :alt: https://github.com/munterfinger/glacier-flow-model
   :align: center

After reaching steady state a change in temperature can be simulated. Simply use
the :code:`simulate` method with a positive or negative temperature change in degrees.
The model changes the temperature gradually and simulates years until it reaches a steady state again.

Heating 4.5°C after initial steady state:

.. code-block:: python

    gfm.simulate(4.5)

.. image:: https://raw.githubusercontent.com/munterfinger/glacier-flow-model/develop/docs/source/_static/steady_state_heating.png
   :width: 120 px
   :alt: https://github.com/munterfinger/glacier-flow-model
   :align: center

Cooling -1°C after initial steady state:

.. code-block:: python

    gfm.simulate(-1)

.. image:: https://raw.githubusercontent.com/munterfinger/glacier-flow-model/develop/docs/source/_static/steady_state_cooling.png
   :width: 120 px
   :alt: https://github.com/munterfinger/glacier-flow-model
   :align: center

Limitations
-----------

The model has some important limitations:

- The flow velocity of the ice per year is limited by the resolution of the grid cells. Therefore, a too high resolution should not be chosen for the simulation.
- The modeling of ice flow is done with D8, a technique for modeling surface flow in hydrology. Water behaves fundamentally different from ice, which is neglected by the model (e.g. influence of crevasses).
- No distinction is made between snow and ice. The density of the snow or ice mass is also neglected in the vertical column.

License
-------

This project is licensed under the MIT License - see the LICENSE file for details
