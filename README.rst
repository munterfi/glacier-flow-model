.. image:: https://raw.githubusercontent.com/munterfi/glacier-flow-model/master/docs/source/_static/logo.svg
   :width: 120 px
   :alt: https://github.com/munterfi/glacier-flow-model
   :align: right

==================
Glacier flow model
==================

.. image:: https://img.shields.io/pypi/v/glacier-flow-model.svg
        :target: https://pypi.python.org/pypi/glacier-flow-model

.. image:: https://github.com/munterfi/glacier-flow-model/workflows/check/badge.svg
        :target: https://github.com/munterfi/glacier-flow-model/actions?query=workflow%3Acheck

.. image:: https://readthedocs.org/projects/glacier-flow-model/badge/?version=latest
        :target: https://glacier-flow-model.readthedocs.io/en/latest/
        :alt: Documentation Status

.. image:: https://codecov.io/gh/munterfi/glacier-flow-model/branch/master/graph/badge.svg
        :target: https://codecov.io/gh/munterfi/glacier-flow-model

Modeling glaciers on a digital elevation model (DEM) based on the mass balance of the glaciers
and the D8 flow algorithm applied to the ice.

The modeling is based on the linear relationship between altitude and mass balance, the so-called mass balance gradient.
For alpine glaciers this gradient is about 0.006 m/m. Continental glaciers tend to be at 0.003 and maritime glaciers
at 0.01 m/m. The alpine gradient is set by default in the model.
To model the glaciers, annual steps are calculated. First the mass balance (accumulation and ablation) for the area
is added to the glacier layer and in a second step the glacier flow is simulated by using the D8 technique,
which is known for modeling surface water flows over the terrain. In order to avoid pure convergence of the flow,
a random impulse ("nudging") is added to the flow. Then the surface of the glaciers is slightly smoothed.
The simulation stops when the observed difference in mass balance for a smoothed curve (n=-100) is less than 0.0001 m.

Getting started
---------------

The **glacier-flow-model** package depends on GDAL, which needs to be installed on the system.

Get the stable release of the package from pypi:

.. code-block:: shell

    pip install glacier-flow-model

Example data
____________

The package includes an example DEM from `swisstopo <https://www.swisstopo.admin.ch/en/home.html>`_.
It covers a smaller extent around the Aletsch glacial arena in Switzerland with a raster cell resolution of 200m.

.. code-block:: python

    from glacier_flow_model import PkgDataAccess
    pkg = PkgDataAccess()
    dem = pkg.load_dem()

The original DEM can be downloaded `here <https://shop.swisstopo.admin.ch/en/products/height_models/dhm25200>`_.

Usage
_____

To set up a glacier flow model, a path to a DEM in the GeoTiff (:code:`.tif` or :code:`.asc`)
file format has to passed to the model class constructor. By default the mass balance parameters for alpine glaciers
in the year 2000 are set.  Keep the input file size small, otherwise the model may be slowed down remarkably:

.. code-block:: python

    from glacier_flow_model import GlacierFlowModel, PkgDataAccess
    pkg = PkgDataAccess()
    gfm = GlacierFlowModel(pkg.locate_dem())

After initialization, the model needs to accumulate the initial ice mass until it reaches a steady state, call the
:code:`reach_steady_state` method to do so:

.. code-block:: python

    gfm.reach_steady_state()

.. image:: https://raw.githubusercontent.com/munterfi/glacier-flow-model/master/docs/source/_static/steady_state_initial.png
   :width: 120 px
   :alt: https://github.com/munterfi/glacier-flow-model
   :align: center

When the model is in a steady state, a temperature change of the climate can be simulated. Simply use
the :code:`simulate` method with a positive or negative temperature change in degrees.
The model changes the temperature gradually and simulates years until it reaches a steady state again.

Heating 4.5°C after initial steady state:

.. code-block:: python

    gfm.simulate(4.5)

.. image:: https://raw.githubusercontent.com/munterfi/glacier-flow-model/master/docs/source/_static/steady_state_heating.png
   :width: 120 px
   :alt: https://github.com/munterfi/glacier-flow-model
   :align: center

Cooling -1°C after initial steady state:

.. code-block:: python

    gfm.simulate(-1)

.. image:: https://raw.githubusercontent.com/munterfi/glacier-flow-model/master/docs/source/_static/steady_state_cooling.png
   :width: 120 px
   :alt: https://github.com/munterfi/glacier-flow-model
   :align: center

Check out the `video <https://munterfi.ch/media/film/gfm.mp4>`_ of the scenario simulation in the Aletsch
glacial arena in Switzerland

Limitations
-----------

The model has some limitations that need to be considered:

- The flow velocity of the ice per year is limited by the resolution of the grid cells. Therefore, a too high resolution should not be chosen for the simulation.
- The modeling of ice flow is done with D8, a technique for modeling surface flow in hydrology. Water behaves fundamentally different from ice, which is neglected by the model (e.g. influence of crevasses).
- No distinction is made between snow and ice. The density of the snow or ice mass is also neglected in the vertical column.

License
-------

This project is licensed under the MIT License - see the LICENSE file for details
