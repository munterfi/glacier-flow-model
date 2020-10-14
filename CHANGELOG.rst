Changelog
=========

This packages uses `semantic versions <https://semver.org/>`_.

Version 0.1.0
------------------

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
    - data: Stores example data.
- Scripts:
    - :code:`install.sh`: Builds the package and installs it to the global python version.
    - :code:`check.sh`: Automates checks and documentation build.
