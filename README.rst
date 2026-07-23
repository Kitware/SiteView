E3SM Site View
----------------------------------------

The SiteView UI presents an ARM observatory as a candidate location for in-depth analysis of simulation results.


.. image:: https://raw.githubusercontent.com/Kitware/SiteView/main/SiteView.png
  :alt: Example of e3sm-siteview data explorer

License
----------------------------------------

This library is OpenSource and follow the Apache Software License

Installation
----------------------------------------

Install the application/library

.. code-block:: console

    pip install e3sm-siteview

Run the application

.. code-block:: console

    e3sm-siteview --cf ../data/connectivity.nc --df ../data/file_1.nc [...] ../data/file_n.nc

Development setup
----------------------------------------

We recommend using uv for setting up and managing a virtual environment for your development.

.. code-block:: console

    # Create venv and install all dependencies
    uv sync --all-extras --dev

    # Activate environment
    source .venv/bin/activate

    # Install commit analysis
    pre-commit install
    pre-commit install --hook-type commit-msg




For running tests and checks, you can run ``nox``.

.. code-block:: console

    # run all
    nox

    # lint
    nox -s lint

    # tests
    nox -s tests

Professional Support
----------------------------------------

* `Training <https://www.kitware.com/courses/trame/>`_: Learn how to confidently use trame from the expert developers at Kitware.
* `Support <https://www.kitware.com/trame/support/>`_: Our experts can assist your team as you build your web application and establish in-house expertise.
* `Custom Development <https://www.kitware.com/trame/support/>`_: Leverage Kitware’s 25+ years of experience to quickly build your web application.
