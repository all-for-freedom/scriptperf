"""
Plotting module for scriptperf.

This module provides functionality to generate performance visualization plots.
"""

import logging
import platform
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import matplotlib

__author__ = "all-for-freedom"
__copyright__ = "all-for-freedom"
__license__ = "MIT"

_logger = logging.getLogger(__name__)

# Configure matplotlib for Chinese font support
# Must be configured before any plotting operations
if platform.system() == "Darwin":
    matplotlib.rcParams["font.sans-serif"] = ["Arial Unicode MS", "PingFang SC", "Hiragino Sans GB"]
elif platform.system() == "Windows":
    matplotlib.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
else:
    matplotlib.rcParams["font.sans-serif"] = ["DejaVu Sans", "WenQuanYi Micro Hei"]

matplotlib.rcParams["axes.unicode_minus"] = False


def plot_performance_data(
    cpu_data: List[float],
    memory_data: List[float],
    timestamps: List[float],
    script_name: str,
    output_path: Path,
    figsize=(12, 6),
    dpi=100,
):
    """Generate a performance plot with CPU and memory usage over time.

    Args:
      cpu_data (List[float]): CPU usage percentages
      memory_data (List[float]): Memory usage in MB
      timestamps (List[float]): Relative timestamps in seconds
      script_name (str): Name of the script being monitored
      output_path (Path): Path where the plot will be saved
      figsize (tuple): Figure size (width, height) in inches (default: (12, 6))
      dpi (int): Resolution in dots per inch (default: 100)
    """
    if not cpu_data or not memory_data or not timestamps:
        _logger.warning("No data to plot")
        return

    if len(cpu_data) != len(memory_data) or len(cpu_data) != len(timestamps):
        _logger.error("Data arrays have different lengths")
        return

    # Create figure with dual y-axes
    fig, ax1 = plt.subplots(figsize=figsize, dpi=dpi)

    # Plot memory on left y-axis
    color_memory = "tab:blue"
    ax1.set_xlabel("时间 (秒)", fontsize=12)
    ax1.set_ylabel("内存占用 (MB)", color=color_memory, fontsize=12)
    line1 = ax1.plot(timestamps, memory_data, color=color_memory, label="内存占用", linewidth=1.5)
    ax1.tick_params(axis="y", labelcolor=color_memory)
    ax1.grid(True, alpha=0.3)

    # Plot CPU on right y-axis
    ax2 = ax1.twinx()
    color_cpu = "tab:orange"
    ax2.set_ylabel("CPU 使用率 (%)", color=color_cpu, fontsize=12)
    line2 = ax2.plot(timestamps, cpu_data, color=color_cpu, label="CPU 使用率", linewidth=1.5)
    ax2.tick_params(axis="y", labelcolor=color_cpu)

    # Add title
    duration = timestamps[-1] if timestamps else 0
    max_cpu = max(cpu_data) if cpu_data else 0
    max_memory = max(memory_data) if memory_data else 0
    title = (
        f"性能监控报告: {script_name}\n"
        f"运行时长: {duration:.2f}秒 | "
        f"峰值 CPU: {max_cpu:.1f}% | "
        f"峰值内存: {max_memory:.1f}MB"
    )
    plt.title(title, fontsize=14, fontweight="bold", pad=20)

    # Add legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper left", fontsize=10)

    # Adjust layout to prevent label cutoff
    fig.tight_layout()

    # Save the plot
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    _logger.info(f"Plot saved to: {output_path}")

    # Close figure to free memory
    plt.close(fig)

