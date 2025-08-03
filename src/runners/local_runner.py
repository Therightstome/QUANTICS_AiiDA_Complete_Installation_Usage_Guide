#!/usr/bin/env python3
"""
QUANTICS Local Runner - Phase 1: Local execution
Goal: Modular design prepared for future integration with AiiDA and Hartree supercomputing
"""

import os
import sys
import subprocess
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse


class QuanticsCalculation:
    """Data structure representing a QUANTICS calculation"""

    def __init__(self, name: str):
        self.name = name
        self.inp_file = None
        self.op_file = None
        self.db_folder = None  # For DD-vMCG
        self.workflow_type = "MCTDH"  # MCTDH, vMCG, DD-vMCG
        self.working_directory = None
        self.status = "created"  # created, running, completed, failed
        self.start_time = None
        self.end_time = None
        self.results = {}

    def to_dict(self) -> Dict:
        """Convert to dictionary for saving and AiiDA integration"""
        return {
            "name": self.name,
            "inp_file": str(self.inp_file) if self.inp_file else None,
            "op_file": str(self.op_file) if self.op_file else None,
            "db_folder": str(self.db_folder) if self.db_folder else None,
            "workflow_type": self.workflow_type,
            "working_directory": str(self.working_directory) if self.working_directory else None,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "results": self.results,
        }

    @classmethod
    def from_dict(cls, data: Dict):
        """Create object from dictionary for data recovery"""
        calc = cls(data["name"])
        calc.inp_file = Path(data["inp_file"]) if data["inp_file"] else None
        calc.op_file = Path(data["op_file"]) if data["op_file"] else None
        calc.db_folder = Path(data["db_folder"]) if data["db_folder"] else None
        calc.workflow_type = data["workflow_type"]
        calc.working_directory = (
            Path(data["working_directory"]) if data["working_directory"] else None
        )
        calc.status = data["status"]
        calc.start_time = datetime.fromisoformat(data["start_time"]) if data["start_time"] else None
        calc.end_time = datetime.fromisoformat(data["end_time"]) if data["end_time"] else None
        calc.results = data["results"]
        return calc


class LocalQuanticsRunner:
    """Local QUANTICS runner - designed for easy AiiDA adaptation in the future"""

    def __init__(self, base_directory: Optional[Path] = None):
        self.base_directory = base_directory or Path.home() / ".quantics_local"
        self.runs_directory = self.base_directory / "runs"
        self.config_file = self.base_directory / "calculations.json"

        # Create necessary directories
        self.base_directory.mkdir(exist_ok=True)
        self.runs_directory.mkdir(exist_ok=True)

        # Load saved calculation records
        self.calculations = self._load_calculations()

    def _load_calculations(self) -> Dict[str, QuanticsCalculation]:
        """Load saved calculation records"""
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                name: QuanticsCalculation.from_dict(calc_data) for name, calc_data in data.items()
            }
        except Exception as e:
            print(f"Warning: Failed to load calculation records: {e}")
            return {}

    def _save_calculations(self):
        """Save calculation records"""
        data = {name: calc.to_dict() for name, calc in self.calculations.items()}
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def create_calculation(
        self,
        name: str,
        inp_file: Path,
        op_file: Path,
        workflow_type: str = "MCTDH",
        db_folder: Optional[Path] = None,
    ) -> QuanticsCalculation:
        """Create new calculation"""
        if name in self.calculations:
            raise ValueError(f"Calculation name '{name}' already exists")

        calc = QuanticsCalculation(name)
        calc.inp_file = Path(inp_file).resolve()
        calc.op_file = Path(op_file).resolve()
        calc.workflow_type = workflow_type

        if workflow_type == "DD-vMCG" and db_folder:
            calc.db_folder = Path(db_folder).resolve()

        # Create working directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        calc.working_directory = self.runs_directory / f"{name}_{timestamp}"
        calc.working_directory.mkdir(exist_ok=True)

        self.calculations[name] = calc
        self._save_calculations()

        return calc

    def prepare_calculation(self, calc: QuanticsCalculation) -> bool:
        """Prepare calculation: copy input files to working directory"""
        try:
            # Copy input file
            shutil.copy2(calc.inp_file, calc.working_directory / "input.inp")

            # Read opname and copy operator file with correct name
            opname = self._get_opname_from_inp(calc.inp_file)
            if opname:
                op_filename = f"{opname}.op"
            else:
                op_filename = "operator.op"  # fallback

            shutil.copy2(calc.op_file, calc.working_directory / op_filename)

            # If DD-vMCG, copy DB folder
            if calc.workflow_type == "DD-vMCG" and calc.db_folder:
                target_db = calc.working_directory / "db_data"
                shutil.copytree(calc.db_folder, target_db)

            print(f"Input files prepared for calculation '{calc.name}'")
            print(f"Operator file copied as: {op_filename}")
            return True

        except Exception as e:
            print(f"Failed to prepare calculation: {e}")
            return False

    def run_calculation(
        self, calc: QuanticsCalculation, quantics_executable: str = "quantics"
    ) -> bool:
        """Run QUANTICS calculation"""
        if calc.status == "running":
            print(f"Calculation '{calc.name}' is already running")
            return False

        # Prepare calculation
        if not self.prepare_calculation(calc):
            return False

        try:
            calc.status = "running"
            calc.start_time = datetime.now()
            self._save_calculations()

            # Build command (add -mnd option to auto-create name directory)
            cmd = [quantics_executable, "-mnd", "input.inp"]

            print(f"Starting calculation '{calc.name}'...")
            print(f"Working directory: {calc.working_directory}")
            print(f"Command: {' '.join(cmd)}")

            # Run calculation
            with open(calc.working_directory / "quantics.log", "w") as log_file:
                process = subprocess.run(
                    cmd,
                    cwd=calc.working_directory,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

            calc.end_time = datetime.now()

            if process.returncode == 0:
                calc.status = "completed"
                print(f"Calculation '{calc.name}' completed successfully")

                # Check output files
                self._check_output_files(calc)

            else:
                calc.status = "failed"
                print(f"Calculation '{calc.name}' failed")
                print(f"See log file: {calc.working_directory / 'quantics.log'}")

            self._save_calculations()
            return calc.status == "completed"

        except Exception as e:
            calc.status = "failed"
            calc.end_time = datetime.now()
            self._save_calculations()
            print(f"Error occurred while running calculation: {e}")
            return False

    def _check_output_files(self, calc: QuanticsCalculation):
        """Check output files and record results"""
        # Try to read actual name from inp file
        output_name = self._get_output_name_from_inp(calc.working_directory / "input.inp")
        if not output_name:
            output_name = calc.name  # fallback

        output_dir = calc.working_directory / output_name
        if output_dir.exists():
            calc.results["output_directory"] = str(output_dir)
            calc.results["output_name"] = output_name  # Save actual output name

            # Check common output files
            expected_files = ["log", "output", "auto", "psi"]
            found_files = []

            for file_name in expected_files:
                if (output_dir / file_name).exists():
                    found_files.append(file_name)

            calc.results["output_files"] = found_files
            print(f"Found output files: {', '.join(found_files)}")
        else:
            print(f"Warning: Output directory not found {output_dir}")

    def _get_output_name_from_inp(self, inp_file_path: Path) -> str:
        """Read output name from .inp file"""
        try:
            with open(inp_file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("name") and "=" in line:
                        name = line.split("=")[1].strip()
                        return name
        except Exception as e:
            print(f"Warning: Cannot read name from inp file: {e}")
        return None

    def _get_opname_from_inp(self, inp_file_path: Path) -> str:
        """Read opname from .inp file"""
        try:
            with open(inp_file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("opname") and "=" in line:
                        opname = line.split("=")[1].strip()
                        return opname
        except Exception as e:
            print(f"Warning: Cannot read opname from inp file: {e}")
        return None

    def run_analysis(self, calc: QuanticsCalculation, analysis_tools: List[str]) -> Dict[str, str]:
        """Run analysis tools"""
        if calc.status != "completed":
            print(f"Calculation '{calc.name}' not completed, cannot run analysis")
            return {}

        # Use saved output name or re-parse
        output_name = calc.results.get("output_name")
        if not output_name:
            output_name = self._get_output_name_from_inp(calc.working_directory / "input.inp")
        if not output_name:
            output_name = calc.name  # fallback

        output_dir = calc.working_directory / output_name
        if not output_dir.exists():
            print(f"Output directory does not exist: {output_dir}")
            return {}

        results = {}

        for tool in analysis_tools:
            try:
                print(f"Running analysis tool: {tool}")

                if tool.startswith("rdcheck"):
                    # rdcheck tool
                    parts = tool.split()
                    cmd = parts  # ["rdcheck", "etot"] or similar

                elif tool == "rdgpop":
                    cmd = ["rdgpop", "-w"]  # Add -w option to auto-overwrite files

                elif tool == "ddtraj":
                    cmd = ["ddtraj"]

                else:
                    print(f"Unknown analysis tool: {tool}")
                    continue

                # Run analysis tool
                if tool == "rdgpop":
                    # rdgpop needs interactive input, provide default values
                    input_text = "2\n1\n"  # nz=2, dof=1 (common default values)
                    result = subprocess.run(
                        cmd, cwd=output_dir, input=input_text, capture_output=True, text=True
                    )
                else:
                    result = subprocess.run(cmd, cwd=output_dir, capture_output=True, text=True)

                if result.returncode == 0:
                    results[tool] = result.stdout
                    print(f"{tool} completed")

                    # Save results to file
                    output_file = output_dir / f"{tool.replace(' ', '_')}_output.txt"
                    with open(output_file, "w") as f:
                        f.write(result.stdout)

                else:
                    results[tool] = f"Error: {result.stderr}"
                    print(f"{tool} failed: {result.stderr}")

            except Exception as e:
                results[tool] = f"Exception: {str(e)}"
                print(f"Exception while running {tool}: {e}")

        # Update calculation record
        calc.results["analysis"] = results
        self._save_calculations()

        return results

    def run_analysis_with_params(
        self, calc: QuanticsCalculation, analysis_tools: List[str], params: Dict[str, str]
    ) -> Dict[str, str]:
        """Run analysis tools (with parameter support)"""
        if calc.status != "completed":
            print(f"Calculation '{calc.name}' not completed, cannot run analysis")
            return {}

        # Use saved output name or re-parse
        output_name = calc.results.get("output_name")
        if not output_name:
            output_name = self._get_output_name_from_inp(calc.working_directory / "input.inp")
        if not output_name:
            output_name = calc.name  # fallback

        output_dir = calc.working_directory / output_name
        if not output_dir.exists():
            print(f"Output directory does not exist: {output_dir}")
            return {}

        results = {}
        show_cmdline = params.get("show_cmdline", True)

        for tool in analysis_tools:
            try:
                print(f"Running analysis tool: {tool}")

                if tool.startswith("rdcheck"):
                    # rdcheck tool
                    parts = tool.split()
                    cmd = parts  # ["rdcheck", "etot"] or similar

                elif tool == "rdgpop":
                    cmd = ["rdgpop", "-w"]  # Add -w option to auto-overwrite files

                elif tool == "ddtraj":
                    cmd = ["ddtraj"]

                else:
                    print(f"Unknown analysis tool: {tool}")
                    continue

                # Run analysis tool
                if tool == "rdgpop":
                    # rdgpop uses user-specified parameters
                    nz = params.get("rdgpop_nz", "2")
                    dof = params.get("rdgpop_dof", "1")
                    input_text = f"{nz}\n{dof}\n"

                    if show_cmdline:
                        print(f"Executing command: {' '.join(cmd)}")
                        print(f"Input parameters: nz={nz}, dof={dof}")
                        print("=" * 50)

                    result = subprocess.run(
                        cmd, cwd=output_dir, input=input_text, capture_output=True, text=True
                    )

                    if show_cmdline and result.stdout:
                        # Display complete command line output
                        print("Command line output:")
                        print(result.stdout)
                        print("=" * 50)

                else:
                    if show_cmdline:
                        print(f"Executing command: {' '.join(cmd)}")
                        print("=" * 50)

                    result = subprocess.run(cmd, cwd=output_dir, capture_output=True, text=True)

                    if show_cmdline and result.stdout:
                        print("Command line output:")
                        print(result.stdout)
                        print("=" * 50)

                if result.returncode == 0:
                    results[tool] = result.stdout
                    print(f"{tool} completed")

                    # Save results to file
                    output_file = output_dir / f"{tool.replace(' ', '_')}_output.txt"
                    with open(output_file, "w") as f:
                        f.write(result.stdout)

                else:
                    results[tool] = f"Error: {result.stderr}"
                    print(f"{tool} failed: {result.stderr}")
                    if show_cmdline and result.stderr:
                        print("Error output:")
                        print(result.stderr)
                        print("=" * 50)

            except Exception as e:
                results[tool] = f"Exception: {str(e)}"
                print(f"Exception while running {tool}: {e}")

        # Update calculation record
        calc.results["analysis_with_params"] = results
        self._save_calculations()

        return results

    def list_calculations(self) -> List[QuanticsCalculation]:
        """List all calculations"""
        return list(self.calculations.values())

    def get_calculation(self, name: str) -> Optional[QuanticsCalculation]:
        """Get calculation with specified name"""
        return self.calculations.get(name)

    def print_status(self):
        """Print status of all calculations"""
        if not self.calculations:
            print("No calculation records found")
            return

        print("\n=== QUANTICS Calculation Status ===")
        print(f"{'Name':<20} {'Status':<10} {'Type':<10} {'Start Time':<20}")
        print("-" * 70)

        for calc in self.calculations.values():
            start_time = (
                calc.start_time.strftime("%Y-%m-%d %H:%M:%S") if calc.start_time else "Not started"
            )
            print(f"{calc.name:<20} {calc.status:<10} {calc.workflow_type:<10} {start_time:<20}")


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(description="QUANTICS Local Runner")
    parser.add_argument("--base-dir", type=Path, help="Base working directory")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create calculation command
    create_parser = subparsers.add_parser("create", help="Create new calculation")
    create_parser.add_argument("name", help="Calculation name")
    create_parser.add_argument("inp_file", type=Path, help=".inp input file path")
    create_parser.add_argument("op_file", type=Path, help=".op operator file path")
    create_parser.add_argument(
        "--workflow", choices=["MCTDH", "vMCG", "DD-vMCG"], default="MCTDH", help="Workflow type"
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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Create runner
    runner = LocalQuanticsRunner(args.base_dir)

    if args.command == "create":
        try:
            calc = runner.create_calculation(
                args.name, args.inp_file, args.op_file, args.workflow, args.db_folder
            )
            print(f"Successfully created calculation '{calc.name}'")
            print(f"Working directory: {calc.working_directory}")
        except Exception as e:
            print(f"Failed to create calculation: {e}")

    elif args.command == "run":
        calc = runner.get_calculation(args.name)
        if not calc:
            print(f"Calculation '{args.name}' not found")
            return

        success = runner.run_calculation(calc, args.quantics_exe)
        if success:
            print(f"Calculation '{args.name}' completed")
        else:
            print(f"Calculation '{args.name}' failed")

    elif args.command == "analyze":
        calc = runner.get_calculation(args.name)
        if not calc:
            print(f"Calculation '{args.name}' not found")
            return

        results = runner.run_analysis(calc, args.tools)
        print(f"\nAnalysis results saved to: {calc.working_directory / calc.name}")

    elif args.command == "status":
        runner.print_status()

    elif args.command == "example":
        # Run example calculation
        example_dir = Path("Exercise_1/ho")
        if example_dir.exists():
            try:
                calc = runner.create_calculation(
                    "ho_example", example_dir / "ho.inp", example_dir / "ho.op", "MCTDH"
                )
                print(f"Created example calculation '{calc.name}'")

                # If quantics executable exists, try to run
                if shutil.which("quantics"):
                    print("Detected quantics executable, starting run...")
                    runner.run_calculation(calc)

                    # Run basic analysis
                    print("Running basic analysis...")
                    runner.run_analysis(calc, ["rdcheck etot", "rdcheck spop"])
                else:
                    print("quantics executable not found, please run manually:")
                    print(f"cd {calc.working_directory} && quantics input.inp")

            except Exception as e:
                print(f"Failed to run example: {e}")
        else:
            print("Example file directory Exercise_1/ho not found")


if __name__ == "__main__":
    main()
