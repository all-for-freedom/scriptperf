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
        self.process_start_time = None  # Process creation time
        self.process_end_time = None  # Process termination time

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
            # Try to get process creation time (more accurate for duration calculation)
            try:
                self.process_start_time = self.process.create_time()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.process_start_time = self.start_time
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
                        # Record process end time for accurate duration calculation
                        try:
                            # Get the actual process end time if available
                            # psutil doesn't directly provide end time, so we use current time
                            # but we'll adjust timestamps later based on actual process runtime
                            self.process_end_time = time.time()
                        except Exception:
                            self.process_end_time = time.time()
                        break

                    # Get current timestamp (relative to process start time, not monitoring start time)
                    current_time = time.time()
                    # Use process creation time for more accurate relative timestamps
                    if self.process_start_time:
                        relative_time = current_time - self.process_start_time
                    else:
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

        # Calculate actual process runtime
        actual_duration = 0.0
        if self.process_start_time and self.process_end_time:
            actual_duration = self.process_end_time - self.process_start_time
        elif self.timestamps:
            # Fallback to last timestamp if we don't have process times
            actual_duration = self.timestamps[-1] if self.timestamps else 0.0
            # But cap it at the actual process runtime if we can determine it
            if self.process and hasattr(self.process, 'create_time'):
                try:
                    if not self.process.is_running():
                        # Process has ended, use last timestamp or process runtime
                        if self.process_start_time:
                            actual_duration = min(actual_duration, time.time() - self.process_start_time)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        _logger.info(
            f"Collected {len(self.timestamps)} data points "
            f"over {actual_duration:.2f} seconds"
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

    def set_process_end_time(self, end_time: Optional[float] = None):
        """Set the process end time.
        
        Args:
          end_time (Optional[float]): Process end time. If None, uses current time.
        """
        if end_time is None:
            end_time = time.time()
        self.process_end_time = end_time

    def get_actual_duration(self) -> float:
        """Get actual process runtime duration.

        Returns:
          float: Actual process runtime in seconds
        """
        if self.process_start_time and self.process_end_time:
            return self.process_end_time - self.process_start_time
        elif self.process_start_time:
            # Check if process is still running
            try:
                if self.process and not self.process.is_running():
                    # Process has ended but we didn't capture end time
                    # Estimate from last timestamp or current time
                    if self.timestamps:
                        # Use last timestamp as approximation
                        return min(self.timestamps[-1], time.time() - self.process_start_time)
                    else:
                        return time.time() - self.process_start_time
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process definitely ended
                if self.timestamps:
                    return min(self.timestamps[-1], time.time() - self.process_start_time)
                else:
                    return time.time() - self.process_start_time if self.process_start_time else 0.0
            # Process still running - shouldn't happen after stop(), but fallback
            if self.timestamps:
                return self.timestamps[-1]
            else:
                return 0.0
        elif self.timestamps:
            # Fallback to last timestamp
            return self.timestamps[-1]
        else:
            return 0.0

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

