"""
Main Window for QUANTICS Professional GUI
========================================

This module contains the main window class with both local and AiiDA execution modes.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# GUI imports
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *

    QT_AVAILABLE = True
except ImportError:
    try:
        from PySide2.QtWidgets import *
        from PySide2.QtCore import *
        from PySide2.QtGui import *

        QT_AVAILABLE = True
    except ImportError:
        QT_AVAILABLE = False
        print("Error: PyQt5 or PySide2 required for GUI")

# Import our modules
from ..runners.local_runner import LocalQuanticsRunner

try:
    from ..runners.aiida_integration import QuanticsAiidaIntegration

    AIIDA_AVAILABLE = True
except ImportError:
    AIIDA_AVAILABLE = False

from ..utils.config import save_config, load_config, get_default_config


class QuanticsMainWindow(QMainWindow):
    """
    Main window for QUANTICS Professional GUI
    Supports both local execution and AiiDA workflow modes
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("QUANTICS Professional GUI")
        self.setGeometry(100, 100, 1600, 1000)

        # Initialize components
        self.local_runner = LocalQuanticsRunner()
        self.current_result_dir = None
        self.runner_thread = None
        self.aiida_enabled = AIIDA_AVAILABLE

        # Workflow analysis tools mapping
        self.workflow_analysis_map = {
            "MCTDH": [
                ("rdcheck etot", "Total energy check"),
                ("rdcheck spop", "Single particle population"),
                ("rdcheck natpop 0 0", "Natural potential analysis"),
                ("rdgpop", "Grid population analysis"),
            ],
            "vMCG": [
                ("rdcheck etot", "Total energy check"),
                ("rdcheck spop", "Single particle population"),
            ],
            "DD-vMCG": [
                ("rdcheck etot", "Total energy check"),
                ("rdcheck spop", "Single particle population"),
                ("ddtraj", "DD trajectory analysis"),
            ],
        }

        # Initialize UI
        self.init_ui()
        self.setup_connections()

        # Set initial status
        status = "Ready (AiiDA enabled)" if self.aiida_enabled else "Ready (local only)"
        self.status_label.setText(status)

    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QHBoxLayout(central_widget)

        # Left panel: Configuration and controls
        left_panel = QVBoxLayout()
        self.create_execution_mode_panel(left_panel)
        self.create_config_panel(left_panel)
        self.create_analysis_panel(left_panel)
        self.create_control_panel(left_panel)

        # Right panel: Logs and results
        right_panel = QVBoxLayout()
        self.create_log_panel(right_panel)
        self.create_results_panel(right_panel)

        # Add panels to main layout
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(600)

        right_widget = QWidget()
        right_widget.setLayout(right_panel)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)

        # Create menu bar and status bar
        self.create_menu_bar()
        self.status_label = QLabel("Initializing...")
        self.statusBar().addWidget(self.status_label)

    def create_execution_mode_panel(self, layout):
        """Create execution mode selection panel"""
        group = QGroupBox("Execution Mode")
        group_layout = QVBoxLayout(group)

        self.execution_mode = QButtonGroup()

        self.local_mode_rb = QRadioButton("Local Execution")
        self.local_mode_rb.setChecked(True)
        self.local_mode_rb.setToolTip("Run calculations on local machine")

        self.aiida_mode_rb = QRadioButton("AiiDA Workflow")
        self.aiida_mode_rb.setEnabled(self.aiida_enabled)
        self.aiida_mode_rb.setToolTip("Submit to AiiDA workflow management")

        if not self.aiida_enabled:
            self.aiida_mode_rb.setText("AiiDA Workflow (not available)")

        self.execution_mode.addButton(self.local_mode_rb, 0)
        self.execution_mode.addButton(self.aiida_mode_rb, 1)

        group_layout.addWidget(self.local_mode_rb)
        group_layout.addWidget(self.aiida_mode_rb)

        layout.addWidget(group)

    def create_config_panel(self, layout):
        """Create configuration panel"""
        # Basic settings
        group = QGroupBox("Basic Settings")
        form_layout = QFormLayout(group)

        self.calc_name_edit = QLineEdit("my_quantics_run")
        form_layout.addRow("Calculation Name:", self.calc_name_edit)

        self.workflow_combo = QComboBox()
        self.workflow_combo.addItems(["MCTDH", "vMCG", "DD-vMCG"])
        self.workflow_combo.currentTextChanged.connect(self.update_analysis_tools)
        form_layout.addRow("Workflow Type:", self.workflow_combo)

        layout.addWidget(group)

        # Input files
        group = QGroupBox("Input Files")
        form_layout = QFormLayout(group)

        # INP file
        inp_layout = QHBoxLayout()
        self.inp_file_edit = QLineEdit()
        inp_browse_btn = QPushButton("Browse")
        inp_browse_btn.clicked.connect(
            lambda: self.browse_file(
                self.inp_file_edit, "Select QUANTICS Input File", "Input files (*.inp)"
            )
        )
        inp_layout.addWidget(self.inp_file_edit)
        inp_layout.addWidget(inp_browse_btn)
        form_layout.addRow(".inp file:", inp_layout)

        # OP file
        op_layout = QHBoxLayout()
        self.op_file_edit = QLineEdit()
        op_browse_btn = QPushButton("Browse")
        op_browse_btn.clicked.connect(
            lambda: self.browse_file(
                self.op_file_edit, "Select QUANTICS Operator File", "Operator files (*.op)"
            )
        )
        op_layout.addWidget(self.op_file_edit)
        op_layout.addWidget(op_browse_btn)
        form_layout.addRow(".op file:", op_layout)

        # DB folder (for DD-vMCG)
        db_layout = QHBoxLayout()
        self.db_folder_edit = QLineEdit()
        db_browse_btn = QPushButton("Browse")
        db_browse_btn.clicked.connect(
            lambda: self.browse_dir(self.db_folder_edit, "Select Database Folder")
        )
        db_layout.addWidget(self.db_folder_edit)
        db_layout.addWidget(db_browse_btn)
        form_layout.addRow("DB folder:", db_layout)

        layout.addWidget(group)

        # Execution settings
        group = QGroupBox("Execution Settings")
        form_layout = QFormLayout(group)

        self.quantics_exec_edit = QLineEdit("quantics")
        form_layout.addRow("QUANTICS Executable:", self.quantics_exec_edit)

        self.work_dir_edit = QLineEdit()
        work_dir_layout = QHBoxLayout()
        work_dir_browse = QPushButton("Browse")
        work_dir_browse.clicked.connect(
            lambda: self.browse_dir(self.work_dir_edit, "Select Working Directory")
        )
        work_dir_layout.addWidget(self.work_dir_edit)
        work_dir_layout.addWidget(work_dir_browse)
        form_layout.addRow("Working Directory:", work_dir_layout)

        layout.addWidget(group)

    def create_analysis_panel(self, layout):
        """Create analysis tools panel"""
        group = QGroupBox("Post-processing Analysis")
        group_layout = QVBoxLayout(group)

        # Tool selection
        self.analysis_list = QListWidget()
        self.analysis_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.analysis_list.setMaximumHeight(120)
        group_layout.addWidget(QLabel("Analysis Tools:"))
        group_layout.addWidget(self.analysis_list)

        # Selection buttons
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_analysis)
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self.select_none_analysis)

        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(select_none_btn)
        group_layout.addLayout(button_layout)

        # Parameters section
        params_group = QGroupBox("Analysis Parameters")
        params_layout = QGridLayout(params_group)

        params_layout.addWidget(QLabel("rdgpop - nz:"), 0, 0)
        self.rdgpop_nz_edit = QLineEdit("2")
        self.rdgpop_nz_edit.setMaximumWidth(60)
        params_layout.addWidget(self.rdgpop_nz_edit, 0, 1)

        params_layout.addWidget(QLabel("rdgpop - dof:"), 0, 2)
        self.rdgpop_dof_edit = QLineEdit("1")
        self.rdgpop_dof_edit.setMaximumWidth(60)
        params_layout.addWidget(self.rdgpop_dof_edit, 0, 3)

        self.show_cmdline_cb = QCheckBox("Show command lines")
        self.show_cmdline_cb.setChecked(True)
        params_layout.addWidget(self.show_cmdline_cb, 1, 0, 1, 4)

        group_layout.addWidget(params_group)

        # Initialize tools
        self.update_analysis_tools("MCTDH")

        layout.addWidget(group)

    def create_control_panel(self, layout):
        """Create control buttons panel"""
        group = QGroupBox("Controls")
        button_layout = QVBoxLayout(group)

        self.start_btn = QPushButton("Start Calculation")
        self.start_btn.clicked.connect(self.start_calculation)
        self.start_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }"
        )

        self.stop_btn = QPushButton("Stop Calculation")
        self.stop_btn.clicked.connect(self.stop_calculation)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)

        layout.addWidget(group)

    def create_log_panel(self, layout):
        """Create log display panel"""
        group = QGroupBox("Calculation Log")
        log_layout = QVBoxLayout(group)

        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        # Log controls
        log_controls = QHBoxLayout()
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.log_text.clear)
        save_log_btn = QPushButton("Save Log")
        save_log_btn.clicked.connect(self.save_log)

        log_controls.addWidget(clear_log_btn)
        log_controls.addWidget(save_log_btn)
        log_controls.addStretch()
        log_layout.addLayout(log_controls)

        layout.addWidget(group)

    def create_results_panel(self, layout):
        """Create results display panel"""
        group = QGroupBox("Results Browser")
        results_layout = QVBoxLayout(group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        results_layout.addWidget(self.progress_bar)

        # Results tree
        self.result_tree = QTreeWidget()
        self.result_tree.setHeaderLabels(["Name", "Size", "Modified"])
        results_layout.addWidget(self.result_tree)

        # Results controls
        results_controls = QHBoxLayout()
        refresh_results_btn = QPushButton("Refresh")
        refresh_results_btn.clicked.connect(self.refresh_results)
        open_dir_btn = QPushButton("Open Directory")
        open_dir_btn.clicked.connect(self.open_result_directory)

        results_controls.addWidget(refresh_results_btn)
        results_controls.addWidget(open_dir_btn)
        results_controls.addStretch()
        results_layout.addLayout(results_controls)

        layout.addWidget(group)

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_action = QAction("New Calculation", self)
        new_action.triggered.connect(self.new_calculation)
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        save_config_action = QAction("Save Configuration", self)
        save_config_action.triggered.connect(self.save_config)
        file_menu.addAction(save_config_action)

        load_config_action = QAction("Load Configuration", self)
        load_config_action.triggered.connect(self.load_config)
        file_menu.addAction(load_config_action)

        # Help menu
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_connections(self):
        """Set up signal connections"""
        self.execution_mode.buttonClicked.connect(self.on_execution_mode_changed)
        self.workflow_combo.currentTextChanged.connect(self.update_analysis_tools)

    def on_execution_mode_changed(self, button):
        """Handle execution mode change"""
        is_aiida = self.execution_mode.checkedId() == 1

        # Update button text
        if is_aiida:
            self.start_btn.setText("Submit to AiiDA")
        else:
            self.start_btn.setText("Start Calculation")

    def start_calculation(self):
        """Start calculation (local or AiiDA)"""
        if not self.validate_inputs():
            return

        config = self.collect_config()

        if self.execution_mode.checkedId() == 1 and self.aiida_enabled:
            # AiiDA mode - implement AiiDA submission
            self.submit_to_aiida(config)
        else:
            # Local mode
            self.start_local_calculation(config)

    def start_local_calculation(self, config):
        """Start local calculation"""
        try:
            # Create calculation
            calc = self.local_runner.create_calculation(
                name=config["calculation_name"],
                inp_file=Path(config["inp_file"]),
                op_file=Path(config["op_file"]),
                workflow_type=config["workflow_type"],
                db_folder=Path(config["db_folder"]) if config.get("db_folder") else None,
            )

            # Update UI
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            self.append_log("=== Starting QUANTICS Calculation ===")
            self.append_log(f"Calculation name: {calc.name}")
            self.append_log(f"Workflow type: {calc.workflow_type}")

            # Run calculation
            success = self.local_runner.run_calculation(
                calc, config.get("quantics_executable", "quantics")
            )

            if success:
                self.append_log("=== Calculation completed successfully ===")
                self.current_result_dir = calc.working_directory

                # Run analysis if selected
                analysis_tools = config.get("analysis_tools", [])
                if analysis_tools:
                    self.append_log("Starting analysis...")
                    analysis_params = {
                        "rdgpop_nz": config.get("rdgpop_nz", "2"),
                        "rdgpop_dof": config.get("rdgpop_dof", "1"),
                        "show_cmdline": config.get("show_cmdline", True),
                    }

                    results = self.local_runner.run_analysis_with_params(
                        calc, analysis_tools, analysis_params
                    )

                    self.append_log("Analysis completed")

                self.load_results(calc.working_directory)
                QMessageBox.information(self, "Success", "Calculation completed successfully!")

            else:
                self.append_log("=== Calculation failed ===")
                QMessageBox.critical(self, "Error", "Calculation failed!")

        except Exception as e:
            self.append_log(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error occurred: {str(e)}")
        finally:
            # Reset UI
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.progress_bar.setVisible(False)

    def submit_to_aiida(self, config):
        """Submit calculation to AiiDA"""
        # Placeholder for AiiDA submission
        QMessageBox.information(self, "AiiDA", "AiiDA submission will be implemented here")

    def validate_inputs(self):
        """Validate user inputs"""
        if not self.calc_name_edit.text().strip():
            QMessageBox.warning(self, "Input Error", "Please provide a calculation name")
            return False

        if not self.inp_file_edit.text() or not Path(self.inp_file_edit.text()).exists():
            QMessageBox.warning(self, "File Error", "Please select a valid .inp file")
            return False

        if not self.op_file_edit.text() or not Path(self.op_file_edit.text()).exists():
            QMessageBox.warning(self, "File Error", "Please select a valid .op file")
            return False

        if self.workflow_combo.currentText() == "DD-vMCG":
            if not self.db_folder_edit.text() or not Path(self.db_folder_edit.text()).exists():
                QMessageBox.warning(
                    self, "Folder Error", "DD-vMCG workflow requires a valid DB folder"
                )
                return False

        return True

    def collect_config(self):
        """Collect configuration from UI"""
        selected_tools = []
        for i in range(self.analysis_list.count()):
            item = self.analysis_list.item(i)
            if item.isSelected():
                tool_cmd = item.text().split(" - ")[0]
                selected_tools.append(tool_cmd)

        return {
            "calculation_name": self.calc_name_edit.text(),
            "workflow_type": self.workflow_combo.currentText(),
            "inp_file": self.inp_file_edit.text(),
            "op_file": self.op_file_edit.text(),
            "db_folder": self.db_folder_edit.text() if self.db_folder_edit.text() else None,
            "quantics_executable": self.quantics_exec_edit.text(),
            "working_directory": self.work_dir_edit.text() if self.work_dir_edit.text() else None,
            "analysis_tools": selected_tools,
            "rdgpop_nz": self.rdgpop_nz_edit.text().strip() or "2",
            "rdgpop_dof": self.rdgpop_dof_edit.text().strip() or "1",
            "show_cmdline": self.show_cmdline_cb.isChecked(),
        }

    def update_analysis_tools(self, workflow_type):
        """Update analysis tools based on workflow type"""
        self.analysis_list.clear()

        if workflow_type in self.workflow_analysis_map:
            tools = self.workflow_analysis_map[workflow_type]
            for tool, description in tools:
                item = QListWidgetItem(f"{tool} - {description}")
                self.analysis_list.addItem(item)

    def select_all_analysis(self):
        """Select all analysis tools"""
        for i in range(self.analysis_list.count()):
            self.analysis_list.item(i).setSelected(True)

    def select_none_analysis(self):
        """Deselect all analysis tools"""
        self.analysis_list.clearSelection()

    def append_log(self, message):
        """Append message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.ensureCursorVisible()

    def browse_file(self, line_edit, title, filter_str):
        """Browse for file"""
        file_path, _ = QFileDialog.getOpenFileName(self, title, "", filter_str)
        if file_path:
            line_edit.setText(file_path)

    def browse_dir(self, line_edit, title):
        """Browse for directory"""
        dir_path = QFileDialog.getExistingDirectory(self, title)
        if dir_path:
            line_edit.setText(dir_path)

    def stop_calculation(self):
        """Stop calculation"""
        # Placeholder for stop functionality
        self.append_log("Stop calculation requested")

    def save_log(self):
        """Save log to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Log",
            f"quantics_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text files (*.txt)",
        )

        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "Success", f"Log saved to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving log: {str(e)}")

    def new_calculation(self):
        """Start new calculation"""
        # Reset all fields to defaults
        self.calc_name_edit.setText("my_quantics_run")
        self.workflow_combo.setCurrentText("MCTDH")
        self.inp_file_edit.clear()
        self.op_file_edit.clear()
        self.db_folder_edit.clear()
        self.quantics_exec_edit.setText("quantics")
        self.work_dir_edit.clear()
        self.analysis_list.clearSelection()
        self.log_text.clear()

    def save_config(self):
        """Save configuration"""
        config = self.collect_config()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Configuration",
            f"quantics_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON files (*.json)",
        )

        if file_path:
            if save_config(config, Path(file_path)):
                QMessageBox.information(self, "Success", f"Configuration saved to: {file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to save configuration")

    def load_config(self):
        """Load configuration"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", "", "JSON files (*.json)"
        )

        if file_path:
            config = load_config(Path(file_path))
            if config:
                # Apply configuration to UI
                self.calc_name_edit.setText(config.get("calculation_name", ""))
                self.workflow_combo.setCurrentText(config.get("workflow_type", "MCTDH"))
                self.inp_file_edit.setText(str(config.get("inp_file", "")))
                self.op_file_edit.setText(str(config.get("op_file", "")))
                self.db_folder_edit.setText(str(config.get("db_folder", "") or ""))
                self.quantics_exec_edit.setText(config.get("quantics_executable", "quantics"))
                self.work_dir_edit.setText(str(config.get("working_directory", "") or ""))
                self.rdgpop_nz_edit.setText(config.get("rdgpop_nz", "2"))
                self.rdgpop_dof_edit.setText(config.get("rdgpop_dof", "1"))
                self.show_cmdline_cb.setChecked(config.get("show_cmdline", True))

                QMessageBox.information(self, "Success", f"Configuration loaded from {file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to load configuration")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About QUANTICS Professional GUI",
            """
                         <h2>QUANTICS Professional GUI</h2>
                         <p><b>Version:</b> 3.0.0</p>
                         <p><b>Advanced quantum dynamics calculation interface</b></p>
                         
                         <h3>Features:</h3>
                         <ul>
                         <li>Local and distributed execution</li>
                         <li>AiiDA workflow management</li>
                         <li>Data provenance tracking</li>
                         <li>Dynamic analysis tools</li>
                         </ul>
                         
                         <p><b>AiiDA Status:</b> %s</p>
                         """
            % ("Enabled" if self.aiida_enabled else "Not Available"),
        )

    def load_results(self, result_dir):
        """Load results to tree view - placeholder"""
        self.append_log(f"Results available in: {result_dir}")
        # TODO: Implement results tree view

    def refresh_results(self):
        """Refresh results display - placeholder"""
        if self.current_result_dir:
            self.load_results(self.current_result_dir)

    def open_result_directory(self):
        """Open results directory - placeholder"""
        if self.current_result_dir and os.path.exists(self.current_result_dir):
            if sys.platform.startswith("win"):
                os.startfile(self.current_result_dir)
            elif sys.platform.startswith("darwin"):
                import subprocess

                subprocess.run(["open", self.current_result_dir])
            else:
                import subprocess

                subprocess.run(["xdg-open", self.current_result_dir])
