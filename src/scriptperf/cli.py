"""
Command-line interface for scriptperf.

This module provides the `spx` command to run Python scripts with performance monitoring.
"""

import argparse
import logging
import subprocess
import sys
import threading
import time
from pathlib import Path
from datetime import datetime

from scriptperf import __version__
from scriptperf.monitor import PerformanceMonitor
from scriptperf.plotter import plot_performance_data

__author__ = "all-for-freedom"
__copyright__ = "all-for-freedom"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(
        description="Run Python script with performance monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  spx demo.py                    # Run demo.py and generate performance report
  spx demo.py --interval 0.2     # Set sampling interval to 0.2 seconds
  spx demo.py --output ./reports # Custom output directory
        """,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"scriptperf {__version__}",
    )
    parser.add_argument(
        "script",
        help="Python script to run",
        type=str,
    )
    parser.add_argument(
        "--interval",
        dest="interval",
        help="Sampling interval in seconds (default: 0.1)",
        type=float,
        default=0.1,
    )
    parser.add_argument(
        "--output",
        dest="output_dir",
        help="Output directory for performance reports (default: ./spx)",
        type=str,
        default="./spx",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )

    # Parse known args to allow passing arguments to the script
    parsed_args, script_args = parser.parse_known_args(args)

    # Add script arguments as a new attribute
    parsed_args.script_args = script_args

    return parsed_args


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel or logging.WARNING,
        stream=sys.stdout,
        format=logformat,
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def run_script(script_path, script_args, monitor):
    """Run the Python script and return the process

    Args:
      script_path (str): Path to the Python script
      script_args (List[str]): Additional arguments to pass to the script
      monitor (PerformanceMonitor): Monitor instance to track the process

    Returns:
      subprocess.Popen: The process object
    """
    # Build command: python script_path [script_args...]
    cmd = [sys.executable, str(script_path)] + script_args

    _logger.debug(f"Executing command: {' '.join(cmd)}")

    # Start the process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # Line buffered
    )

    # Register the process with the monitor
    monitor.set_process(process)

    return process


def main(args=None):
    """Main entry point for the spx command

    Args:
      args (List[str]): command line parameters (default: None, uses sys.argv)
    """
    if args is None:
        args = sys.argv[1:]

    # Parse arguments
    parsed_args = parse_args(args)
    setup_logging(parsed_args.loglevel)

    # Validate script path
    script_path = Path(parsed_args.script)
    if not script_path.exists():
        _logger.error(f"Script not found: {script_path}")
        sys.exit(1)

    if not script_path.is_file():
        _logger.error(f"Path is not a file: {script_path}")
        sys.exit(1)

    # Create output directory
    output_dir = Path(parsed_args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    _logger.info(f"Starting performance monitoring for: {script_path}")
    _logger.debug(f"Sampling interval: {parsed_args.interval}s")

    # Create monitor
    monitor = PerformanceMonitor(interval=parsed_args.interval)

    try:
        # Run the script first (this sets the process in monitor)
        process = run_script(script_path, parsed_args.script_args, monitor)

        # Start monitoring thread (after process is set)
        monitor.start()

        # Wait for the process to complete and capture output
        stdout, stderr = process.communicate()

        # Record process end time before stopping monitoring
        monitor.set_process_end_time(time.time())

        # Stop monitoring
        monitor.stop()

        # Get performance data
        cpu_data = monitor.get_cpu_data()
        memory_data = monitor.get_memory_data()
        timestamps = monitor.get_timestamps()
        actual_duration = monitor.get_actual_duration()

        # Generate output filename
        script_name = script_path.stem
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_filename = f"{script_name}-{timestamp}.png"
        output_path = output_dir / output_filename

        # Generate performance plot (always generate, even if data is empty)
        _logger.info(f"Generating performance report: {output_path}")
        plot_performance_data(
            cpu_data=cpu_data if cpu_data else [],
            memory_data=memory_data if memory_data else [],
            timestamps=timestamps if timestamps else [],
            script_name=script_name,
            output_path=output_path,
            actual_duration=actual_duration,
        )
        print(f"\n✓ Performance report saved to: {output_path}")
        
        if not cpu_data or not memory_data:
            _logger.info("Script executed too quickly to collect performance data, but chart was still generated")

        # Print original script output
        if stdout:
            sys.stdout.write(stdout)
        if stderr:
            sys.stderr.write(stderr)

        # Exit with the same code as the script
        sys.exit(process.returncode)

    except KeyboardInterrupt:
        _logger.info("Interrupted by user")
        monitor.stop()
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        _logger.exception(f"Unexpected error: {e}")
        monitor.stop()
        sys.exit(1)


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main()


if __name__ == "__main__":
    run()

