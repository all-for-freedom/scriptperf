==========
scriptperf
==========

Run Python scripts with performance monitoring (CPU and memory usage tracking).

Installation
------------

.. code-block:: bash

    pip install scriptperf

Usage
-----

.. code-block:: bash

    # Run a script with performance monitoring
    spx demo.py

    # Custom sampling interval and output directory
    spx demo.py --interval 0.2 --output ./reports

    # Pass arguments to the script
    spx demo.py --arg1 value1 --arg2 value2

Features
--------

- Real-time CPU and memory usage monitoring
- Automatic performance report generation (PNG charts)
- Support for passing arguments to monitored scripts
- Configurable sampling interval and output directory

Requirements
------------

- Python 3.8+
- psutil>=5.9.0
- matplotlib>=3.5.0

Repository
----------

https://github.com/all-for-freedom/scriptperf

License
-------

MIT License
