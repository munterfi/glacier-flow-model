Changelog
=========

This packages uses `semantic versioning <https://semver.org/>`_.

Version 0.2.0
-------------

- Features:
    - Use of the :code:`.flake8` config file.
    - Configured Dependabot.
    - Add :code:`CITATION.cff` file for citing the repository and linking to zenodo for DOI generation.
    - Use python :code:`logging` module and remove inheritance from :code:`Base` class.
    - Added :code:`tolerance` as class instance variable of the :code:`GlacierFowModel` class.
    - Use internal method :code:`self._iterate` to simluate years in order to reduce duplicate code.
    - Getter and setter methods for the :code:`plot` instance variable, which initializes or destroys the :code:`matplotlib.pyplot.figure`.
- Bugfixes:
    - Fix failing CI: Update package dependencies, set GitHub actions to python 3.10, set GDAL version to 3.4.1 and remove shebang from tests.
    - Updated mypy configuration.

Version 0.1.2
-------------

- Bugfixes:
    - Format shell scripts.
    - Adjust URLs to GitHub account due to renaming munterfinger to munterfi.

Version 0.1.1
-------------

- Features:
    - New issue templates for bug reports and feature requests.
    - Documentation and PyPI link in the project description.
- Bugfixes:
    - Typo in documentation link.
    - Force install from :code:`.whl` in :code:`install.sh` script.

Version 0.1.0
-------------

- Initial release of the **glacier-flow-model** on pypi.org package; a python tool to model glacier flow.
- Development setup:
    - :code:`poetry`: Managing dependencies and package build env.
    - :code:`pytest`: Framework for testing.
    - :code:`mypy`: Static type checking.
    - :code:`flake8`: Code linting.
    - :code:`sphinx`: Documentation of the package using :code:`numpydoc` docstring style.
- Submodules:
    - model: The :code:`GlacierFlowModel` class.
    - internal: Base class and internals.
    - data: Stores example data, which can be accessed using the :code:`PkgDataAccess` class.
- Scripts:
    - :code:`install.sh`: Builds the package and installs it to the global python version.
    - :code:`check.sh`: Automates checks and documentation build.
