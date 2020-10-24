============
Installation
============

System dependencies
-------------------

The **glacier-flow-model** package depends on GDAL, which needs to be installed on the system.

macOS (using homebrew):

.. code-block:: shell

    brew install gdal

Linux (using aptitude):

.. code-block:: shell

    sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable \
        && sudo apt-get update \
        && sudo apt-get install -y gdal-bin libgdal-dev

    export CPLUS_INCLUDE_PATH=/usr/include/gdal
    export C_INCLUDE_PATH=/usr/include/gdal

    python3 -m pip install --upgrade pip \
        && python3 -m pip install numpy \
        && python3 -m pip install \
            --global-option=build_ext \
            --global-option="-I/usr/include/gdal" \
            GDAL==`gdal-config --version`

Windows (using conda):

.. code-block:: shell

    conda install -c conda-forge gdal

Stable release
--------------

After installing GDAL, get the stable release of **glacier-flow-model** from pypi:

.. code-block:: shell

    python3 -m pip install glacier-flow-model

From sources
------------

Or install the development version from `Github <https://github.com/munterfinger/glacier-flow-model>`_:

.. code-block:: shell

    git clone git://github.com/munterfinger/glacier-flow-model.git
    cd glacier-flow-model
    poetry install && poetry build
    cd dist && python3 -m pip install --upgrade *.whl
