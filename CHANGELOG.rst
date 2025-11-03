=========
Changelog
=========

Version 0.0.2 (unreleased)
===========================

Bugfixes
--------

- Fixed issue where empty or very fast-running scripts would not generate performance charts
- Performance charts are now always generated, even when script execution time is too short to collect data

Version 0.0.1 (2025-11-03)
==========================

Initial release.

Features
--------

- Added ``spx`` command-line tool for running Python scripts with performance monitoring
- Real-time CPU and memory usage monitoring
- Automatic performance report generation (PNG charts with dual Y-axis)
- Support for passing arguments to monitored scripts
- Configurable sampling interval and output directory
- Chinese font support for matplotlib charts
