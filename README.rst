E3SM Site View
----------------------------------------

The SiteView UI presents an ARM observatory as a candidate location for in-depth analysis of simulation results.
It extracts the E3SM atmosphere (EAM) columns around a site of interest and lets you explore how their fields evolve in space and time.

.. image:: https://raw.githubusercontent.com/Kitware/SiteView/main/SiteView.png
  :alt: Example of e3sm-siteview data explorer with the 3D view, column heatmap and time charts

Features
----------------------------------------

* **Guided setup**: pick the site (from the ARM user facilities or any latitude/longitude), the radius of the region of interest and the fields to load.
* **3D view** of the selected columns with toggleable layers: clouds, vertical scaling, surface, volume, horizontal and vertical slices, find data, histogram, column cropping and probes. The view can be saved as an image.
* **Column heatmap** showing a field over vertical levels and time for a given column.
* **Cell time charts** comparing one or more fields across several columns over time.
* Heatmaps and charts can be downloaded.
* **Time animation** with play/pause and step controls across all the loaded files.
* Light and dark themes.

.. image:: https://raw.githubusercontent.com/Kitware/SiteView/main/SiteView-setup.png
  :alt: Site and region selection step of e3sm-siteview

License
----------------------------------------

This library is open source and follows the Apache Software License. See `LICENSE <https://github.com/Kitware/SiteView/blob/main/LICENSE>`_ for details.

Installation
----------------------------------------

SiteView requires Python 3.12 or newer.

.. code-block:: console

    pip install e3sm-siteview

Input data
----------------------------------------

SiteView reads E3SM atmosphere (EAM) output in NetCDF format:

* ``--cf``: the connectivity file describing the horizontal mesh (SCRIP/TEMPEST format, e.g. ``connectivity_ne30pg2_TEMPEST.scrip.nc``).
  Both global and regional meshes are supported, as long as they match the data files.
* ``--df``: one or more EAM history files (e.g. ``*.eam.h1.*.nc``) holding the fields to explore.
  When several files are given, each one gets its own panel and they all share a single time control.
  The time steps are read from the first file only: all the files are assumed to share the same time steps.

Running the application
----------------------------------------

.. code-block:: console

    e3sm-siteview --cf ../data/connectivity.nc --df ../data/file_1.nc [...] ../data/file_n.nc

For example, with a regional dataset:

.. code-block:: console

    e3sm-siteview \
        --cf data/regional/connectivity_ne30pg2_170e_to_230e_55n_to_85n_TEMPEST.nc \
        --df data/regional/v2_F20TR_nc00_ndgAllLevs_pd.eam.h1.2008-07-*.nc

By default a browser tab opens on the application. Useful options:

=====================  ==============================================================
Option                 Description
=====================  ==============================================================
``--server``           Do not open a browser at startup (e.g. when running remotely)
``-p, --port PORT``    Port to serve the application on
``--host HOST``        Network interface to bind to (use ``0.0.0.0`` to allow remote access)
``--perf``             Print performance timing on stderr (``[PERF]`` lines)
=====================  ==============================================================

Run ``e3sm-siteview --help`` for the full list of options.

Keyboard shortcuts
----------------------------------------

Once the data is loaded, the following shortcuts are available (they are ignored while typing in a field or when a setup dialog is open).

=============  ==============================================================
Key            Action
=============  ==============================================================
``Space``      Play / pause the time animation
``←`` / ``→``  Previous / next time step (hold to keep stepping)
``R``          Reset the camera
``1`` - ``9``  Toggle the 3D view layers, in the order of the left toolbar
``0``          Toggle the 10th layer (Probes)
=============  ==============================================================

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

Examples
----------------------------------------

The `examples <https://github.com/Kitware/SiteView/tree/main/examples>`_ directory contains standalone scripts that use the bundled EAM VTK readers
(``e3sm_siteview.io``) directly, without the UI: reading the mesh and column data, building the 3D column volume,
selecting columns within a radius and extracting time series.

Contributing
----------------------------------------

See `CONTRIBUTING.rst <https://github.com/Kitware/SiteView/blob/main/CONTRIBUTING.rst>`_ for how to contribute and `CHANGELOG.md <https://github.com/Kitware/SiteView/blob/main/CHANGELOG.md>`_ for the release history.

Professional Support
----------------------------------------

* `Training <https://www.kitware.com/courses/trame/>`_: Learn how to confidently use trame from the expert developers at Kitware.
* `Support <https://www.kitware.com/trame/support/>`_: Our experts can assist your team as you build your web application and establish in-house expertise.
* `Custom Development <https://www.kitware.com/trame/support/>`_: Leverage Kitware’s 25+ years of experience to quickly build your web application.
