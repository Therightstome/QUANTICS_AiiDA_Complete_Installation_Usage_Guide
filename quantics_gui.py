#!/usr/bin/env python3
"""
QUANTICS Professional GUI - Main Entry Point
===========================================

A professional interface for QUANTICS quantum dynamics calculations
with support for both local execution and AiiDA workflow management.

Usage:
    python quantics_gui.py                    # Start GUI
    python quantics_gui.py --help             # Show help
    python quantics_gui.py create ...         # Command line interface
    python quantics_gui.py gui --mode local   # Start GUI in local mode only

Author: QUANTICS Team
Version: 3.0.0
"""

import sys
import os
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import argument parser
from utils.argument_parser import parse_args


def main():
    """Main entry point"""
    args = parse_args()

    # If no command specified or gui command, start GUI
    if not args.command or args.command == "gui":
        start_gui(getattr(args, "mode", "auto"))
    else:
        # Handle command line interface
        handle_cli_commands(args)


def start_gui(mode="auto"):
    """Start the GUI interface"""
    try:
        # Import GUI components
        from src.gui.main_window import QuanticsMainWindow

        # Check PyQt availability
        try:
            from PyQt5.QtWidgets import QApplication
        except ImportError:
            try:
                from PySide2.QtWidgets import QApplication
            except ImportError:
                print("Error: PyQt5 or PySide2 required for GUI")
                print("Install with: pip install PyQt5")
                sys.exit(1)

        # Create and run application
        app = QApplication(sys.argv)
        app.setApplicationName("QUANTICS Professional GUI")
        app.setApplicationVersion("3.0.0")
        app.setOrganizationName("QUANTICS Team")

        # Create main window
        window = QuanticsMainWindow()

        # Handle mode preference
        if mode == "local":
            # Force local mode
            window.aiida_mode_rb.setEnabled(False)
            window.local_mode_rb.setChecked(True)
        elif mode == "aiida":
            # Prefer AiiDA mode if available
            if window.aiida_enabled:
                window.aiida_mode_rb.setChecked(True)

        window.show()

        # Start event loop
        sys.exit(app.exec_())

    except ImportError as e:
        print(f"Error importing GUI components: {e}")
        print("\nMake sure you have installed all dependencies:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting GUI: {e}")
        sys.exit(1)


def handle_cli_commands(args):
    """Handle command line interface commands"""
    try:
        from runners.local_runner import LocalQuanticsRunner
        import shutil

        # Create runner
        runner = LocalQuanticsRunner(args.base_dir)

        if args.command == "create":
            # Create new calculation
            try:
                calc = runner.create_calculation(
                    args.name, args.inp_file, args.op_file, args.workflow, args.db_folder
                )
                print(f"Successfully created calculation '{calc.name}'")
                print(f"Working directory: {calc.working_directory}")
            except Exception as e:
                print(f"Failed to create calculation: {e}")
                sys.exit(1)

        elif args.command == "run":
            # Run calculation
            calc = runner.get_calculation(args.name)
            if not calc:
                print(f"Calculation '{args.name}' not found")
                sys.exit(1)

            success = runner.run_calculation(calc, args.quantics_exe)
            if success:
                print(f"Calculation '{args.name}' completed successfully")
            else:
                print(f"Calculation '{args.name}' failed")
                sys.exit(1)

        elif args.command == "analyze":
            # Run analysis
            calc = runner.get_calculation(args.name)
            if not calc:
                print(f"Calculation '{args.name}' not found")
                sys.exit(1)

            results = runner.run_analysis(calc, args.tools)
            print(f"\nAnalysis results saved to: {calc.working_directory}")

        elif args.command == "status":
            # Show status
            runner.print_status()

        elif args.command == "example":
            # Run example calculation
            run_example(runner)

    except ImportError as e:
        print(f"Error importing runner components: {e}")
        print("Make sure quantics_local_runner is available")
        sys.exit(1)
    except Exception as e:
        print(f"Error in command line interface: {e}")
        sys.exit(1)


def run_example(runner):
    """Run example calculation"""
    example_dir = Path("examples/example_inputs")
    if not example_dir.exists():
        example_dir = Path("Exercise_1/ho")

    if example_dir.exists():
        try:
            calc = runner.create_calculation(
                "example_run", example_dir / "ho.inp", example_dir / "ho.op", "MCTDH"
            )
            print(f"Created example calculation '{calc.name}'")

            # Check if quantics is available
            import shutil

            if shutil.which("quantics"):
                print("Detected quantics executable, starting run...")
                success = runner.run_calculation(calc)

                if success:
                    # Run basic analysis
                    print("Running basic analysis...")
                    runner.run_analysis(calc, ["rdcheck etot", "rdcheck spop"])
                    print("Example completed successfully!")
                else:
                    print("Example calculation failed")
            else:
                print("quantics executable not found, please run manually:")
                print(f"cd {calc.working_directory} && quantics -mnd input.inp")

        except Exception as e:
            print(f"Failed to run example: {e}")
    else:
        print("Example files not found")
        print("Please ensure example input files are available in examples/example_inputs/")


def check_dependencies():
    """Check if required dependencies are available"""
    missing = []

    # Check PyQt
    try:
        import PyQt5.QtWidgets
    except ImportError:
        try:
            import PySide2.QtWidgets
        except ImportError:
            missing.append("PyQt5 or PySide2")

    # Check other dependencies
    try:
        from pathlib import Path
    except ImportError:
        missing.append("pathlib")

    if missing:
        print("Missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstall with: pip install -r requirements.txt")
        return False

    return True


if __name__ == "__main__":
    # Check dependencies before starting
    if not check_dependencies():
        sys.exit(1)

    main()
