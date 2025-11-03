"""
Performance monitoring module for scriptperf.

This module provides functionality to monitor CPU and memory usage of a running process.
"""

import logging
import threading
import time
from typing import List, Optional

import psutil

__author__ = "all-for-freedom"
__copyright__ = "all-for-freedom"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor CPU and memory usage of a process."""

    def __init__(self, interval: float = 0.1):
        """Initialize the performance monitor.

        Args:
          interval (float): Sampling interval in seconds (default: 0.1)
        """
        self.interval = interval
        self.process: Optional[psutil.Process] = None
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None

        # Data storage
        self.timestamps: List[float] = []
        self.cpu_percentages: List[float] = []
        self.memory_mb: List[float] = []

        # For CPU percentage calculation
        self.last_cpu_times = None
        self.start_time = None

    def set_process(self, process):
        """Set the process to monitor.

        Args:
          process: subprocess.Popen process object or psutil.Process
        """
        try:
            # If it's a subprocess.Popen, get the PID and create psutil.Process
            if hasattr(process, "pid"):
                self.process = psutil.Process(process.pid)
            elif isinstance(process, psutil.Process):
                self.process = process
            else:
                raise ValueError("Invalid process object")

            self.start_time = time.time()
            _logger.debug(f"Monitoring process PID: {self.process.pid}")

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            _logger.error(f"Failed to access process: {e}")
            raise

    def _monitor_loop(self):
        """Main monitoring loop (runs in a separate thread)."""
        if not self.process:
            _logger.error("No process set for monitoring")
            return

        try:
            while self.monitoring:
                try:
                    # Check if process is still running
                    if not self.process.is_running():
                        _logger.debug("Process has terminated")
                        break

                    # Get current timestamp (relative to start)
                    current_time = time.time()
                    relative_time = current_time - self.start_time

                    # Get CPU percentage
                    # Using interval=None with cpu_percent() gives non-blocking call
                    cpu_percent = self.process.cpu_percent(interval=None)

                    # For the first call, cpu_percent() might return 0
                    # We need to wait a bit and call again
                    if len(self.cpu_percentages) == 0:
                        time.sleep(0.1)
                        cpu_percent = self.process.cpu_percent(interval=None)

                    # Get memory info (RSS in bytes, convert to MB)
                    memory_info = self.process.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)

                    # Store data
                    self.timestamps.append(relative_time)
                    self.cpu_percentages.append(cpu_percent)
                    self.memory_mb.append(memory_mb)

                    _logger.debug(
                        f"t={relative_time:.2f}s: CPU={cpu_percent:.1f}%, "
                        f"Memory={memory_mb:.1f}MB"
                    )

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process has terminated or access denied
                    _logger.debug("Process no longer accessible")
                    break
                except Exception as e:
                    _logger.warning(f"Error during monitoring: {e}")

                # Sleep for the sampling interval
                time.sleep(self.interval)

        except Exception as e:
            _logger.error(f"Monitoring loop error: {e}")

    def start(self):
        """Start the monitoring thread."""
        if self.monitoring:
            _logger.warning("Monitoring already started")
            return

        if not self.process:
            raise ValueError("No process set. Call set_process() first.")

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        _logger.debug("Monitoring thread started")

    def stop(self):
        """Stop the monitoring thread."""
        if not self.monitoring:
            return

        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            _logger.debug("Monitoring thread stopped")

        _logger.info(
            f"Collected {len(self.timestamps)} data points "
            f"over {self.timestamps[-1] if self.timestamps else 0:.2f} seconds"
        )

    def get_cpu_data(self) -> List[float]:
        """Get CPU usage data.

        Returns:
          List[float]: CPU usage percentages
        """
        return self.cpu_percentages.copy()

    def get_memory_data(self) -> List[float]:
        """Get memory usage data.

        Returns:
          List[float]: Memory usage in MB
        """
        return self.memory_mb.copy()

    def get_timestamps(self) -> List[float]:
        """Get timestamp data.

        Returns:
          List[float]: Relative timestamps in seconds
        """
        return self.timestamps.copy()

    def get_summary(self) -> dict:
        """Get summary statistics.

        Returns:
          dict: Summary statistics including max, min, mean for CPU and memory
        """
        if not self.cpu_percentages or not self.memory_mb:
            return {}

        return {
            "duration": self.timestamps[-1] if self.timestamps else 0.0,
            "samples": len(self.timestamps),
            "cpu": {
                "max": max(self.cpu_percentages),
                "min": min(self.cpu_percentages),
                "mean": sum(self.cpu_percentages) / len(self.cpu_percentages),
            },
            "memory": {
                "max": max(self.memory_mb),
                "min": min(self.memory_mb),
                "mean": sum(self.memory_mb) / len(self.memory_mb),
            },
        }

