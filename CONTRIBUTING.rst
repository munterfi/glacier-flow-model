Contributing
============

This document contains guidelines for the collaboration in the
**glacier-flow-model** python package.

Getting started
---------------

Ready to contribute? Here's how to set up **glacier-flow-model** for local development.

1. Clone the repository: :code:`git clone https://github.com/munterfi/glacier-flow-model.git`
2. Install the dependencies: :code:`poetry install`
3. Create a feature branch for local development: :code:`git checkout -b feature/<the-feature-name> master`
4. Work locally on the feature, make sure to add or adjust:
    - entries in CHANGELOG.md
    - docstrings
    - tests for the feature
    - documentation
5. When finished with the feature, check that the changes pass:

.. code-block:: shell

        poetry run pytest                               # Running tests
        poetry run mypy .                               # Static type checks
        poetry run flake8 glacier_flow_model tests      # Code linting
        cd docs && poetry run make html && cd ..        # Build documentation

Alternatively the script :code:`check.sh` automates the steps above.

6. If tests are passed commit and push the changes:

.. code-block:: shell

        git add .
        git commit -m "Description of the changes."
        git push origin feature/<the-feature-name>

7. Submit a pull request of the feature into the :code:`master` branch on GitHub.

Trunk-based Development Workflow
--------------------------------
The `trunk-based development workflow <https://trunkbaseddevelopment.com>`_ uses one branch :code:`master` to record the history of the project.
In addition to the mainline short-lived feature or bugfix branches are used to develop new features or fix bugs.

Features
________

Each new feature should reside in its own short-lived branch. Branch off of a :code:`feature/<feature-description>` branch from :code:`master`.
When a feature is complete, it gets merged back into :code:`master` and the feature branch is deleted.

Bugfix
______

Each bugfix should reside in its own short-lived branch. Branch off of a :code:`bugfix/<bugfix-description>` branch from :code:`master`.
When the fix is complete, it gets merged back into :code:`master` and the bugfix branch is deleted.

Release
_______
This packages uses `semantic versioning <https://semver.org/>`_. Once :code:`master` has acquired enough features for a release,
set the new version number of the in the :code:`pyproject.toml` and the :code:`CHANGELOG:rst` file. Commit and push to :code:`master`
and publish a new release on `GitHub <https://github.com/munterfi/glacier-flow-model/releases>`_, which will trigger an action to build
and publish the package to PyPi.

Dependencies
------------
Dependencies and virtual environments are managed by `poetry <https://python-poetry.org/docs/>`_, do not edit the requirements manually!
E.g. use :code:`poetry update && poetry build` for version updating and :code:`poetry add <package_1> <package_2>` for adding new ones.

Documentation and coding style
------------------------------

Naming convention
_________________

Use :code:`snake_case` for variable, argument and function/method name definitions.
Also in tables that are written to the database avoid capital letters and
dots (:code:`.`) in column name definitions. For class names use :code:`UpperCaseCamelCase`.

Python docstrings
_________________

Create python documentation with docstrings in
`numpydoc <https://numpydoc.readthedocs.io/en/latest/format.html>`_ convention.

Example:

.. code-block:: python

    def function_with_types_in_docstring(param1: str, param2: int = 10):
        """Example function with types documented in the docstring.

        `PEP 484`_ type annotations are supported. If attribute, parameter, and
        return types are annotated according to `PEP 484`_, they do not need to be
        included in the docstring:

        Parameters
        ----------
        param1 : str
            The first parameter.
        param2 : int, default 10
            The second parameter.

        Returns
        -------
        bool
            True if successful, False otherwise.

        .. _PEP 484:
            https://www.python.org/dev/peps/pep-0484/

        """

Script header template
______________________

Add a header to CLI scripts according to the following template:

.. code-block:: shell

    #!/usr/bin/env bash
    # -----------------------------------------------------------------------------
    # Name          :example_script.sh
    # Description   :Short description of the scripts purpose.
    # Author        :Full name <your@email.ch>
    # Date          :YYYY-MM-DD
    # Version       :0.1.0
    # Usage         :./example_script.sh
    # Notes         :Is there something important to consider when executing the
    #                script?
    # =============================================================================

Credits
-------

Depending on the scope of your contribution add yourself to the authors field in the :code:`pyproject.toml` file
to ensure credits are given correctly.
