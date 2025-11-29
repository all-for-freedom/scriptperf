"""
Command-line interface for scriptperf.

This module provides the `spx` command to run Python scripts.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from scriptperf import __version__

__author__ = "all-for-freedom"
__copyright__ = "all-for-freedom"
__license__ = "MIT"


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(
        description="Run Python scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
    # 允许传递额外的参数给脚本
    parser.add_argument(
        "script_args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to the script",
    )
    return parser.parse_args(args)


def main(args=None):
    """Main entry point for the spx command

    Args:
      args (List[str]): command line parameters (default: None, uses sys.argv)
    """
    if args is None:
        args = sys.argv[1:]

    # 解析参数
    parsed_args = parse_args(args)

    # 检查脚本文件是否存在
    script_path = Path(parsed_args.script)
    if not script_path.exists():
        print(f"Error: Script not found: {script_path}", file=sys.stderr)
        sys.exit(1)

    if not script_path.is_file():
        print(f"Error: Path is not a file: {script_path}", file=sys.stderr)
        sys.exit(1)

    # 构建命令: python script.py [script_args...]
    cmd = [sys.executable, str(script_path)] + parsed_args.script_args

    # 执行脚本
    try:
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main()


if __name__ == "__main__":
    run()

