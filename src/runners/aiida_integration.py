#!/usr/bin/env python3
"""
QUANTICS AiiDA Integration Module
=================================

This module provides integration between QUANTICS GUI and AiiDA workflow management platform.
It enables automated workflow management, data provenance tracking, and high-throughput calculations.

Features:
- AiiDA-compatible QUANTICS calculation node
- Workflow management and dependency tracking
- Automatic data provenance and storage
- Integration with existing QUANTICS GUI
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

try:
    from aiida import orm
    from aiida.engine import CalcJob, WorkChain, calcfunction, submit, run
    from aiida.common.datastructures import CalcInfo, CodeInfo
    from aiida.plugins import DataFactory, CalculationFactory
    from aiida.parsers.parser import Parser
    from aiida.common.exceptions import NotExistent

    AIIDA_AVAILABLE = True
except ImportError:
    AIIDA_AVAILABLE = False
    print("Warning: AiiDA not available. Install with: pip install aiida-core")

# Import our existing modules
try:
    from quantics_local_runner import LocalQuanticsRunner, QuanticsCalculation
except ImportError:
    print("Warning: quantics_local_runner not found in current directory")


class QuanticsAiidaCalculation(CalcJob):
    """
    AiiDA calculation class for QUANTICS

    This class wraps QUANTICS calculations in AiiDA's calculation framework,
    enabling workflow management and data provenance tracking.
    """

    @classmethod
    def define(cls, spec):
        """Define the process specification"""
        super().define(spec)

        # Define inputs
        spec.input(
            "metadata.options.resources",
            valid_type=dict,
            default=lambda: {"num_machines": 1, "tot_num_mpiprocs": 1},
        )
        spec.input("metadata.options.max_wallclock_seconds", valid_type=int, default=3600)

        # QUANTICS specific inputs
        spec.input("inp_file", valid_type=orm.SinglefileData, help="QUANTICS input file (.inp)")
        spec.input("op_file", valid_type=orm.SinglefileData, help="QUANTICS operator file (.op)")
        spec.input(
            "db_folder",
            valid_type=orm.FolderData,
            required=False,
            help="Database folder for DD-vMCG calculations",
        )
        spec.input(
            "workflow_type",
            valid_type=orm.Str,
            default=lambda: orm.Str("MCTDH"),
            help="Workflow type: MCTDH, vMCG, or DD-vMCG",
        )
        spec.input(
            "analysis_tools",
            valid_type=orm.List,
            required=False,
            help="List of analysis tools to run",
        )
        spec.input(
            "analysis_params",
            valid_type=orm.Dict,
            required=False,
            help="Parameters for analysis tools",
        )

        # Define outputs
        spec.output("output_folder", valid_type=orm.FolderData, help="Complete output folder")
        spec.output("results", valid_type=orm.Dict, help="Parsed calculation results")
        spec.output(
            "analysis_results", valid_type=orm.Dict, required=False, help="Analysis tool results"
        )

        # Define exit codes
        spec.exit_code(100, "ERROR_MISSING_INPUT_FILES", message="Required input files not found")
        spec.exit_code(200, "ERROR_QUANTICS_FAILED", message="QUANTICS calculation failed")
        spec.exit_code(300, "ERROR_ANALYSIS_FAILED", message="Analysis tools failed")

    def prepare_for_submission(self, folder):
        """Prepare the calculation for submission"""

        # Create calculation info
        calcinfo = CalcInfo()

        # Copy input files
        inp_file = self.inputs.inp_file
        op_file = self.inputs.op_file

        # Write input files to calculation folder
        with folder.open("input.inp", "wb") as f:
            f.write(inp_file.get_content(mode="rb"))
        with folder.open("input.op", "wb") as f:
            f.write(op_file.get_content(mode="rb"))

        # Copy database folder if provided (DD-vMCG)
        if "db_folder" in self.inputs:
            db_folder = self.inputs.db_folder
            db_target = folder.get_subfolder("database", create=True)
            for filename in db_folder.list_object_names():
                with db_target.open(filename, "wb") as target_file:
                    target_file.write(db_folder.get_object_content(filename, mode="rb"))

        # Create run script
        run_script = self._create_run_script()
        with folder.open("run_quantics.sh", "w") as f:
            f.write(run_script)

        # Set up code info
        codeinfo = CodeInfo()
        codeinfo.cmdline_params = ["./run_quantics.sh"]
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.stdout_name = "quantics.out"
        codeinfo.stderr_name = "quantics.err"

        calcinfo.codes_info = [codeinfo]
        calcinfo.retrieve_list = ["quantics.out", "quantics.err", "output/*"]

        return calcinfo

    def _create_run_script(self):
        """Create the run script for QUANTICS"""
        workflow_type = self.inputs.workflow_type.value

        script = """#!/bin/bash
set -e

# Run QUANTICS calculation
quantics input.inp > quantics.out 2> quantics.err

# Create output directory
mkdir -p output

# Copy output files
if [ -f "restart" ]; then
    cp restart output/
fi
if [ -f "check" ]; then
    cp check output/
fi
if [ -f "gridpop" ]; then
    cp gridpop output/
fi

# Run analysis tools if specified
"""

        if "analysis_tools" in self.inputs:
            analysis_tools = self.inputs.analysis_tools.get_list()
            analysis_params = (
                self.inputs.analysis_params.get_dict() if "analysis_params" in self.inputs else {}
            )

            for tool in analysis_tools:
                if tool == "rdgpop":
                    nz = analysis_params.get("rdgpop_nz", "2")
                    dof = analysis_params.get("rdgpop_dof", "1")
                    script += f"""
echo "Running {tool}..."
echo -e "{nz}\\n{dof}" | {tool} -w > output/{tool}_output.txt 2>&1
"""
                else:
                    script += f"""
echo "Running {tool}..."
{tool} > output/{tool}_output.txt 2>&1
"""

        script += """
echo "QUANTICS calculation completed"
"""
        return script


class QuanticsAiidaParser(Parser):
    """
    Parser for QUANTICS AiiDA calculations
    """

    def parse(self, **kwargs):
        """Parse the output of a QUANTICS calculation"""

        try:
            # Get output folder
            output_folder = orm.FolderData()

            # Check if calculation completed successfully
            try:
                with self.retrieved.open("quantics.out", "r") as f:
                    stdout_content = f.read()
            except OSError:
                return self.exit_codes.ERROR_QUANTICS_FAILED

            # Parse main results
            results = self._parse_quantics_output(stdout_content)

            # Parse analysis results if available
            analysis_results = {}
            output_files = self.retrieved.list_object_names("output")

            for filename in output_files:
                if filename.endswith("_output.txt"):
                    tool_name = filename.replace("_output.txt", "")
                    try:
                        with self.retrieved.open(f"output/{filename}", "r") as f:
                            analysis_results[tool_name] = f.read()
                    except OSError:
                        continue

            # Store outputs
            self.out("results", orm.Dict(dict=results))
            if analysis_results:
                self.out("analysis_results", orm.Dict(dict=analysis_results))

            # Create output folder
            if self.retrieved.list_object_names("output"):
                output_folder_node = orm.FolderData()
                for filename in self.retrieved.list_object_names("output"):
                    output_folder_node.put_object_from_filelike(
                        self.retrieved.open(f"output/{filename}", "rb"), filename
                    )
                self.out("output_folder", output_folder_node)

            return None

        except Exception as e:
            self.logger.error(f"Error during parsing: {str(e)}")
            return self.exit_codes.ERROR_QUANTICS_FAILED

    def _parse_quantics_output(self, stdout_content: str) -> Dict[str, Any]:
        """Parse QUANTICS output for key results"""
        results = {}

        lines = stdout_content.split("\n")
        for i, line in enumerate(lines):
            # Parse energy information
            if "Total energy" in line:
                try:
                    energy = float(line.split()[-1])
                    results["total_energy"] = energy
                except (ValueError, IndexError):
                    pass

            # Parse time information
            if "Final time" in line:
                try:
                    final_time = float(line.split()[-1])
                    results["final_time"] = final_time
                except (ValueError, IndexError):
                    pass

            # Parse convergence information
            if "Convergence" in line and "achieved" in line:
                results["converged"] = True
            elif "Convergence" in line and "failed" in line:
                results["converged"] = False

        return results


class QuanticsWorkChain(WorkChain):
    """
    WorkChain for QUANTICS calculations with automatic analysis

    This workflow runs a QUANTICS calculation and automatically performs
    analysis based on the workflow type.
    """

    @classmethod
    def define(cls, spec):
        """Define the workchain specification"""
        super().define(spec)

        # Define inputs
        spec.input("quantics_code", valid_type=orm.Code)
        spec.input("inp_file", valid_type=orm.SinglefileData)
        spec.input("op_file", valid_type=orm.SinglefileData)
        spec.input("db_folder", valid_type=orm.FolderData, required=False)
        spec.input("workflow_type", valid_type=orm.Str, default=lambda: orm.Str("MCTDH"))
        spec.input("run_analysis", valid_type=orm.Bool, default=lambda: orm.Bool(True))
        spec.input("analysis_params", valid_type=orm.Dict, required=False)

        # Define workflow steps
        spec.outline(cls.run_quantics, cls.check_quantics, cls.run_analysis, cls.finalize_results)

        # Define outputs
        spec.output("calculation_results", valid_type=orm.Dict)
        spec.output("analysis_results", valid_type=orm.Dict, required=False)
        spec.output("output_folder", valid_type=orm.FolderData)

        # Define exit codes
        spec.exit_code(400, "ERROR_QUANTICS_CALCULATION_FAILED", "The QUANTICS calculation failed")
        spec.exit_code(500, "ERROR_ANALYSIS_FAILED", "The analysis step failed")

    def run_quantics(self):
        """Run the main QUANTICS calculation"""

        # Determine analysis tools based on workflow type
        workflow_type = self.inputs.workflow_type.value
        analysis_tools = self._get_analysis_tools(workflow_type)

        # Set up calculation inputs with proper SGE resources
        # Check if we're using SGE scheduler (hartree)
        computer = self.inputs.quantics_code.computer
        scheduler_type = computer.scheduler_type

        if scheduler_type == "core.sge":
            # SGE scheduler requires parallel_env and tot_num_mpiprocs only
            resources = {
                "parallel_env": "smp",  # Default SGE parallel environment
                "tot_num_mpiprocs": 1,
            }
        else:
            # Other schedulers (PBS, SLURM, etc.) use num_machines format
            resources = {"num_machines": 1, "tot_num_mpiprocs": 1}

        inputs = {
            "code": self.inputs.quantics_code,
            "inp_file": self.inputs.inp_file,
            "op_file": self.inputs.op_file,
            "workflow_type": self.inputs.workflow_type,
            "metadata": {
                "options": {
                    "resources": resources,
                    "max_wallclock_seconds": 3600,
                }
            },
        }

        # Add optional inputs
        if "db_folder" in self.inputs:
            inputs["db_folder"] = self.inputs.db_folder

        if self.inputs.run_analysis.value and analysis_tools:
            inputs["analysis_tools"] = orm.List(list=analysis_tools)
            if "analysis_params" in self.inputs:
                inputs["analysis_params"] = self.inputs.analysis_params

        # Submit calculation
        future = self.submit(QuanticsAiidaCalculation, **inputs)
        return self.to_context(quantics_calc=future)

    def check_quantics(self):
        """Check if QUANTICS calculation completed successfully"""
        calc = self.ctx.quantics_calc

        if not calc.is_finished_ok:
            self.report("QUANTICS calculation failed")
            return self.exit_codes.ERROR_QUANTICS_CALCULATION_FAILED

        self.report("QUANTICS calculation completed successfully")

    def run_analysis(self):
        """Run additional analysis if needed"""
        calc = self.ctx.quantics_calc

        # Additional analysis can be implemented here
        # For now, we use the analysis results from the main calculation

        self.report("Analysis completed")

    def finalize_results(self):
        """Finalize and organize results"""
        calc = self.ctx.quantics_calc

        # Collect outputs
        self.out("calculation_results", calc.outputs.results)
        self.out("output_folder", calc.outputs.output_folder)

        if "analysis_results" in calc.outputs:
            self.out("analysis_results", calc.outputs.analysis_results)

        self.report("WorkChain completed successfully")

    def _get_analysis_tools(self, workflow_type: str) -> List[str]:
        """Get analysis tools based on workflow type"""
        analysis_map = {
            "MCTDH": ["rdcheck etot", "rdcheck spop", "rdcheck natpop 0 0", "rdgpop"],
            "vMCG": ["rdcheck etot", "rdcheck spop"],
            "DD-vMCG": ["rdcheck etot", "rdcheck spop", "ddtraj"],
        }
        return analysis_map.get(workflow_type, [])


class QuanticsAiidaIntegration:
    """
    Integration layer between QUANTICS GUI and AiiDA

    This class provides methods to submit QUANTICS calculations to AiiDA
    and retrieve results for display in the GUI.
    """

    def __init__(self, profile_name: Optional[str] = None, code_label: Optional[str] = None):
        """Initialize AiiDA integration"""
        if not AIIDA_AVAILABLE:
            raise ImportError("AiiDA is not available. Please install with: pip install aiida-core")

        # Load AiiDA profile
        try:
            from aiida.manage import get_manager
            from aiida import load_profile

            # Check if profile is already loaded
            try:
                manager = get_manager()
                current_profile = manager.get_profile()
                if current_profile is None:
                    if profile_name:
                        load_profile(profile_name)
                    else:
                        load_profile()
            except:
                # Profile not loaded, load it
                if profile_name:
                    load_profile(profile_name)
                else:
                    load_profile()

        except Exception as e:
            raise RuntimeError(f"Failed to load AiiDA profile: {e}")

        self.quantics_code = None
        self._setup_code(code_label)

    def _setup_code(self, code_label: str = None):
        """Set up QUANTICS code in AiiDA"""
        try:
            # Try different code options in order of preference
            code_options = [
                code_label,  # User specified
                "quantics-hartree-fixed@hartree",  # Remote cluster (fixed path)
                "quantics-hartree@hartree",  # Remote cluster (old path)
                "quantics@localhost",  # Local
            ]

            for code_option in code_options:
                if code_option:
                    try:
                        self.quantics_code = orm.load_code(code_option)
                        self.report(f"Using QUANTICS code: {code_option}")
                        return
                    except NotExistent:
                        continue

            # If no code found, list available codes
            query = orm.QueryBuilder()
            query.append(orm.Code, filters={"label": {"like": "%quantics%"}})
            available_codes = query.all()

            if available_codes:
                self.report("Available QUANTICS codes:")
                for code_node in available_codes:
                    code = code_node[0]
                    self.report(f"  - {code.full_label} (PK: {code.pk})")
                # Use the first available code
                self.quantics_code = available_codes[0][0]
                self.report(f"Using: {self.quantics_code.full_label}")
            else:
                self.report("No QUANTICS code found in AiiDA. Please set up with:")
                self.report(
                    "verdi code setup --label quantics --computer localhost --remote-abs-path /path/to/quantics"
                )

        except Exception as e:
            self.report(f"Error setting up code: {e}")

    def submit_calculation(
        self,
        inp_file: Path,
        op_file: Path,
        workflow_type: str = "MCTDH",
        db_folder: Optional[Path] = None,
        run_analysis: bool = True,
        analysis_params: Optional[Dict] = None,
    ) -> orm.ProcessNode:
        """
        Submit a QUANTICS calculation to AiiDA

        Args:
            inp_file: Path to .inp file
            op_file: Path to .op file
            workflow_type: Type of workflow (MCTDH, vMCG, DD-vMCG)
            db_folder: Path to database folder (for DD-vMCG)
            run_analysis: Whether to run analysis tools
            analysis_params: Parameters for analysis tools

        Returns:
            Submitted process node
        """

        if not self.quantics_code:
            raise ValueError("QUANTICS code not set up in AiiDA")

        # Create input data nodes
        inp_data = orm.SinglefileData(file=str(inp_file))
        op_data = orm.SinglefileData(file=str(op_file))

        inputs = {
            "quantics_code": self.quantics_code,
            "inp_file": inp_data,
            "op_file": op_data,
            "workflow_type": orm.Str(workflow_type),
            "run_analysis": orm.Bool(run_analysis),
        }

        # Add database folder if provided
        if db_folder and db_folder.exists():
            db_data = orm.FolderData()
            for file_path in db_folder.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(db_folder)
                    db_data.put_object_from_file(str(file_path), str(relative_path))
            inputs["db_folder"] = db_data

        # Add analysis parameters
        if analysis_params:
            inputs["analysis_params"] = orm.Dict(dict=analysis_params)

        # Submit workchain
        process = submit(QuanticsWorkChain, **inputs)

        self.report(f"Submitted QUANTICS calculation with PK: {process.pk}")
        return process

    def get_calculation_status(self, process_pk: int) -> Dict[str, Any]:
        """Get status of a calculation"""
        try:
            process = orm.load_node(process_pk)

            status = {
                "pk": process.pk,
                "label": process.label or f"QUANTICS_{process.pk}",
                "state": (
                    process.process_state.value if hasattr(process, "process_state") else "unknown"
                ),
                "created": process.ctime.isoformat(),
                "finished": process.mtime.isoformat() if process.is_finished else None,
                "exit_status": process.exit_status,
                "has_outputs": bool(process.outputs),
            }

            return status

        except Exception as e:
            return {"error": str(e)}

    def get_calculation_results(self, process_pk: int) -> Dict[str, Any]:
        """Get results from a completed calculation"""
        try:
            process = orm.load_node(process_pk)

            if not process.is_finished_ok:
                return {"error": "Calculation not completed successfully"}

            results = {}

            # Get main calculation results
            if "calculation_results" in process.outputs:
                results["calculation"] = process.outputs.calculation_results.get_dict()

            # Get analysis results
            if "analysis_results" in process.outputs:
                results["analysis"] = process.outputs.analysis_results.get_dict()

            # Get output files information
            if "output_folder" in process.outputs:
                output_folder = process.outputs.output_folder
                results["output_files"] = output_folder.list_object_names()

            return results

        except Exception as e:
            return {"error": str(e)}

    def list_calculations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent QUANTICS calculations"""
        try:
            query = orm.QueryBuilder()
            query.append(QuanticsWorkChain, project=["id", "label", "ctime", "process_state"])
            query.order_by({QuanticsWorkChain: {"ctime": "desc"}})
            query.limit(limit)

            calculations = []
            for pk, label, ctime, state in query.all():
                calculations.append(
                    {
                        "pk": pk,
                        "label": label or f"QUANTICS_{pk}",
                        "created": ctime.isoformat(),
                        "state": state.value if state else "unknown",
                    }
                )

            return calculations

        except Exception as e:
            return [{"error": str(e)}]

    def report(self, message: str):
        """Report a message"""
        print(f"[QuanticsAiidaIntegration] {message}")


# Example usage and helper functions
def setup_aiida_for_quantics():
    """Helper function to set up AiiDA for QUANTICS"""
    if not AIIDA_AVAILABLE:
        print("AiiDA not available. Install with: pip install aiida-core")
        return False

    print("Setting up AiiDA for QUANTICS...")
    print("1. Create AiiDA profile:")
    print("   verdi quicksetup")
    print("2. Set up computer:")
    print("   verdi computer setup")
    print("3. Set up QUANTICS code:")
    print(
        "   verdi code setup --label quantics --computer localhost --remote-abs-path $(which quantics)"
    )
    print("4. Start daemon:")
    print("   verdi daemon start")

    return True


if __name__ == "__main__":
    # Example usage
    if AIIDA_AVAILABLE:
        print("AiiDA integration module loaded successfully")
        print("Available classes:")
        print("- QuanticsAiidaCalculation: AiiDA calculation class")
        print("- QuanticsAiidaParser: Output parser")
        print("- QuanticsWorkChain: Complete workflow")
        print("- QuanticsAiidaIntegration: GUI integration layer")
    else:
        print("AiiDA not available. Run setup_aiida_for_quantics() for instructions.")
        setup_aiida_for_quantics()
