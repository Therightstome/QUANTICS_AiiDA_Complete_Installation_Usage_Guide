"""
Command Line Argument Parser for QUANTICS Professional GUI
=========================================================

This module provides command line argument parsing functionality
that was originally embedded in the main runner.
"""

import argparse
from pathlib import Path


def create_argument_parser():
    """Create and configure the argument parser"""
    parser = argparse.ArgumentParser(
        description="QUANTICS Professional GUI - Local and AiiDA Execution"
    )
    parser.add_argument("--base-dir", type=Path, help="Base working directory")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create calculation command
    create_parser = subparsers.add_parser("create", help="Create new calculation")
    create_parser.add_argument("name", help="Calculation name")
    create_parser.add_argument("inp_file", type=Path, help=".inp input file path")
    create_parser.add_argument("op_file", type=Path, help=".op operator file path")
    create_parser.add_argument(
        "--workflow",
        choices=["MCTDH", "vMCG", "DD-vMCG"],
        default="MCTDH",
        help="Workflow type",
    )
    create_parser.add_argument("--db-folder", type=Path, help="DB data folder (DD-vMCG specific)")

    # Run calculation command
    run_parser = subparsers.add_parser("run", help="Run calculation")
    run_parser.add_argument("name", help="Calculation name")
    run_parser.add_argument("--quantics-exe", default="quantics", help="QUANTICS executable path")

    # Analysis command
    analysis_parser = subparsers.add_parser("analyze", help="Run analysis")
    analysis_parser.add_argument("name", help="Calculation name")
    analysis_parser.add_argument("tools", nargs="+", help="Analysis tools list")

    # Status command
    subparsers.add_parser("status", help="Show calculation status")

    # Example command
    subparsers.add_parser("example", help="Run example calculation")

    # GUI command
    gui_parser = subparsers.add_parser("gui", help="Start GUI interface")
    gui_parser.add_argument(
        "--mode",
        choices=["local", "aiida", "auto"],
        default="auto",
        help="GUI execution mode",
    )

    return parser


def parse_args(args=None):
    """Parse command line arguments"""
    parser = create_argument_parser()
    return parser.parse_args(args)
