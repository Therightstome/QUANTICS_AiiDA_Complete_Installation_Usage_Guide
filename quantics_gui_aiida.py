#!/usr/bin/env python3
"""
QUANTICS Professional GUI with AiiDA Integration
===============================================

Enhanced QUANTICS GUI that integrates with AiiDA workflow management platform.
Provides both local execution and AiiDA-managed distributed computing capabilities.

Features:
- All original QUANTICS GUI features
- AiiDA workflow submission and monitoring
- Distributed computing support
- Advanced workflow management
- Data provenance tracking
"""

import sys
import os
import json
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# GUI imports
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    QT_AVAILABLE = True
    qt_app = QApplication
except ImportError:
    try:
        from PySide2.QtWidgets import *
        from PySide2.QtCore import *
        from PySide2.QtGui import *
        QT_AVAILABLE = True
        qt_app = QApplication
    except ImportError:
        QT_AVAILABLE = False
        print("Error: PyQt5 or PySide2 required for GUI")

# Import local modules
from quantics_local_runner import LocalQuanticsRunner
try:
    from quantics_aiida_integration import QuanticsAiidaIntegration, AIIDA_AVAILABLE
except ImportError:
    AIIDA_AVAILABLE = False
    print("Warning: AiiDA integration not available")

# Import the proven QuanticsRunner class from the original GUI
try:
    from quantics_gui_pyqt import QuanticsRunner
    LOCAL_RUNNER_AVAILABLE = True
except ImportError:
    LOCAL_RUNNER_AVAILABLE = False
    print("Warning: QuanticsRunner from quantics_gui_pyqt not available")


class AiidaWorkerThread(QThread):
    """Worker thread for AiiDA operations"""
    
    status_updated = pyqtSignal(str, dict)  # process_pk, status
    calculation_finished = pyqtSignal(str, bool, dict)  # process_pk, success, results
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.aiida_integration = None
        self.monitoring_processes = set()
        self.should_stop = False
        
    def setup_aiida(self, profile_name=None):
        """Set up AiiDA integration"""
        try:
            self.aiida_integration = QuanticsAiidaIntegration(profile_name)
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to setup AiiDA: {str(e)}")
            return False
    
    def submit_calculation(self, inp_file, op_file, workflow_type, db_folder=None, 
                          run_analysis=True, analysis_params=None):
        """Submit calculation to AiiDA"""
        try:
            if not self.aiida_integration:
                raise ValueError("AiiDA not initialized")
            
            process = self.aiida_integration.submit_calculation(
                inp_file, op_file, workflow_type, db_folder, 
                run_analysis, analysis_params
            )
            
            # Start monitoring this process
            self.monitoring_processes.add(str(process.pk))
            return process.pk
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to submit calculation: {str(e)}")
            return None
    
    def run(self):
        """Monitor AiiDA calculations"""
        while not self.should_stop:
            if self.aiida_integration and self.monitoring_processes:
                for process_pk in list(self.monitoring_processes):
                    try:
                        status = self.aiida_integration.get_calculation_status(int(process_pk))
                        self.status_updated.emit(process_pk, status)
                        
                        # Check if calculation is finished
                        if status.get('state') in ['finished', 'excepted', 'killed']:
                            results = self.aiida_integration.get_calculation_results(int(process_pk))
                            success = 'error' not in results
                            self.calculation_finished.emit(process_pk, success, results)
                            self.monitoring_processes.discard(process_pk)
                            
                    except Exception as e:
                        self.error_occurred.emit(f"Error monitoring process {process_pk}: {str(e)}")
                        self.monitoring_processes.discard(process_pk)
            
            self.msleep(5000)  # Check every 5 seconds
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.should_stop = True


class QuanticsAiidaMainWindow(QMainWindow):
    """
    Main window for QUANTICS GUI with AiiDA integration
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QUANTICS Professional GUI with AiiDA")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize components
        self.local_runner = LocalQuanticsRunner()
        self.aiida_worker = AiidaWorkerThread()
        self.current_result_dir = None
        self.aiida_calculations = {}  # pk -> calculation info
        
        # Local calculation runner (from proven quantics_gui_pyqt.py)
        self.runner_thread = None
        
        # Workflow analysis tools mapping (from quantics_gui_pyqt.py)
        self.workflow_analysis_map = {
            'MCTDH': [
                ('rdcheck etot', 'Total energy check'),
                ('rdcheck spop', 'Single particle population'), 
                ('rdcheck natpop 0 0', 'Natural potential analysis'),
                ('rdgpop', 'Grid population analysis')
            ],
            'vMCG': [
                ('rdcheck etot', 'Total energy check'),
                ('rdcheck spop', 'Single particle population')
            ],
            'DD-vMCG': [
                ('rdcheck etot', 'Total energy check'),
                ('rdcheck spop', 'Single particle population'),
                ('ddtraj', 'DD trajectory analysis')
            ]
        }
        
        # Initialize AiiDA status early
        self.aiida_enabled = False
        
        # Initialize UI first
        self.init_ui()
        
        # Setup AiiDA after UI is initialized
        if AIIDA_AVAILABLE:
            self.setup_aiida()
        else:
            self.status_label.setText("Ready (AiiDA not available)")
        
        # Update UI based on AiiDA status
        self.update_aiida_ui()
        
        self.setup_connections()
        
        # Start AiiDA worker if available
        if self.aiida_enabled:
            self.aiida_worker.start()
    
    def setup_aiida(self):
        """Set up AiiDA integration"""
        try:
            success = self.aiida_worker.setup_aiida()
            if success:
                self.aiida_enabled = True
                self.status_label.setText("Ready (AiiDA enabled)")
            else:
                self.aiida_enabled = False
                self.status_label.setText("Ready (local only)")
        except Exception as e:
            self.aiida_enabled = False
            self.status_label.setText("Ready (AiiDA setup failed)")
            print(f"AiiDA setup failed: {e}")
    
    def update_aiida_ui(self):
        """Update UI elements based on AiiDA availability"""
        # Enable/disable AiiDA mode radio button
        if hasattr(self, 'aiida_mode_rb'):
            self.aiida_mode_rb.setEnabled(self.aiida_enabled)
            if not self.aiida_enabled:
                self.aiida_mode_rb.setText("AiiDA Workflow (not available)")
        
        # Show/hide AiiDA monitor panel
        if hasattr(self, 'aiida_monitor_group'):
            self.aiida_monitor_group.setVisible(self.aiida_enabled)
        
        # Update menu actions
        self.create_menu_bar()  # Recreate menu to update enabled states
    
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel: Configuration and controls
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        
        # Add execution mode selection
        self.create_execution_mode_panel(left_panel)
        
        # Configuration panels
        self.create_config_panel(left_panel)
        self.create_analysis_panel(left_panel)
        self.create_control_panel(left_panel)
        
        # Right panel: Logs and results
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
        
        self.create_log_panel(right_panel)
        self.create_aiida_monitor_panel(right_panel)
        self.create_results_panel(right_panel)
        
        # Add panels to main layout
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(500)
        
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_label = QLabel("Ready")
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
        self.aiida_mode_rb.setEnabled(AIIDA_AVAILABLE)  # Use AIIDA_AVAILABLE instead
        self.aiida_mode_rb.setToolTip("Submit to AiiDA workflow management")
        
        self.execution_mode.addButton(self.local_mode_rb, 0)
        self.execution_mode.addButton(self.aiida_mode_rb, 1)
        
        group_layout.addWidget(self.local_mode_rb)
        group_layout.addWidget(self.aiida_mode_rb)
        
        if not AIIDA_AVAILABLE:
            self.aiida_mode_rb.setText("AiiDA Workflow (not available)")
        
        layout.addWidget(group)
    
    def create_config_panel(self, layout):
        """Create configuration panel"""
        # Basic settings
        group = QGroupBox("Basic Settings")
        form_layout = QFormLayout(group)
        
        self.calc_name_edit = QLineEdit("my_quantics_run")
        self.calc_name_edit.textChanged.connect(self.check_calculation_name)
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
        inp_browse_btn.clicked.connect(lambda: self.browse_file(
            self.inp_file_edit, "Select QUANTICS Input File", "Input files (*.inp)"))
        inp_layout.addWidget(self.inp_file_edit)
        inp_layout.addWidget(inp_browse_btn)
        form_layout.addRow(".inp file:", inp_layout)
        
        # OP file
        op_layout = QHBoxLayout()
        self.op_file_edit = QLineEdit()
        op_browse_btn = QPushButton("Browse")
        op_browse_btn.clicked.connect(lambda: self.browse_file(
            self.op_file_edit, "Select QUANTICS Operator File", "Operator files (*.op)"))
        op_layout.addWidget(self.op_file_edit)
        op_layout.addWidget(op_browse_btn)
        form_layout.addRow(".op file:", op_layout)
        
        # DB folder (for DD-vMCG)
        db_layout = QHBoxLayout()
        self.db_folder_edit = QLineEdit()
        db_browse_btn = QPushButton("Browse")
        db_browse_btn.clicked.connect(lambda: self.browse_dir(
            self.db_folder_edit, "Select Database Folder"))
        db_layout.addWidget(self.db_folder_edit)
        db_layout.addWidget(db_browse_btn)
        form_layout.addRow("DB folder:", db_layout)
        
        self.db_folder_label = form_layout.labelForField(db_layout)
        
        layout.addWidget(group)
        
        # Execution settings
        group = QGroupBox("Execution Settings")
        form_layout = QFormLayout(group)
        
        self.quantics_exec_edit = QLineEdit("quantics")
        form_layout.addRow("QUANTICS Executable:", self.quantics_exec_edit)
        
        self.work_dir_edit = QLineEdit()
        work_dir_layout = QHBoxLayout()
        work_dir_browse = QPushButton("Browse")
        work_dir_browse.clicked.connect(lambda: self.browse_dir(
            self.work_dir_edit, "Select Working Directory"))
        work_dir_layout.addWidget(self.work_dir_edit)
        work_dir_layout.addWidget(work_dir_browse)
        form_layout.addRow("Working Directory:", work_dir_layout)
        
        # AiiDA specific settings
        self.aiida_settings_group = QGroupBox("AiiDA Settings")
        aiida_layout = QFormLayout(self.aiida_settings_group)
        
        self.resources_edit = QLineEdit("1")
        aiida_layout.addRow("Number of cores:", self.resources_edit)
        
        self.walltime_edit = QLineEdit("3600")
        aiida_layout.addRow("Walltime (seconds):", self.walltime_edit)
        
        self.queue_edit = QLineEdit("")
        aiida_layout.addRow("Queue name (optional):", self.queue_edit)
        
        layout.addWidget(group)
        layout.addWidget(self.aiida_settings_group)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        self.save_inputs_cb = QCheckBox("Save input files")
        self.save_inputs_cb.setChecked(True)
        options_layout.addWidget(self.save_inputs_cb)
        
        self.cleanup_cb = QCheckBox("Clean up on success")
        options_layout.addWidget(self.cleanup_cb)
        
        layout.addWidget(options_group)
    
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
        
        # rdgpop parameters
        params_layout.addWidget(QLabel("rdgpop - nz (grid points):"), 0, 0)
        self.rdgpop_nz_edit = QLineEdit("2")
        self.rdgpop_nz_edit.setToolTip("Number of grid points to sum (recommended: 2-3)")
        self.rdgpop_nz_edit.setMaximumWidth(60)
        params_layout.addWidget(self.rdgpop_nz_edit, 0, 1)
        
        params_layout.addWidget(QLabel("rdgpop - dof:"), 0, 2)
        self.rdgpop_dof_edit = QLineEdit("1")
        self.rdgpop_dof_edit.setToolTip("Degree of freedom number (0=max only, 1+=specific DOF)")
        self.rdgpop_dof_edit.setMaximumWidth(60)
        params_layout.addWidget(self.rdgpop_dof_edit, 0, 3)
        
        # Show command line option
        self.show_cmdline_cb = QCheckBox("Show command lines")
        self.show_cmdline_cb.setChecked(True)
        params_layout.addWidget(self.show_cmdline_cb, 1, 0, 1, 4)
        
        group_layout.addWidget(params_group)
        
        # Parameters preview button
        params_btn = QPushButton("Preview Parameters")
        params_btn.clicked.connect(self.preview_analysis_params)
        group_layout.addWidget(params_btn)
        
        # Initialize tools
        self.update_analysis_tools("MCTDH")
        
        layout.addWidget(group)
    
    def create_control_panel(self, layout):
        """Create control buttons panel"""
        group = QGroupBox("Controls")
        button_layout = QVBoxLayout(group)
        
        # Main action buttons
        self.start_btn = QPushButton("Start Calculation")
        self.start_btn.clicked.connect(self.start_calculation)
        self.start_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        
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
    
    def create_aiida_monitor_panel(self, layout):
        """Create AiiDA calculation monitoring panel"""
        group = QGroupBox("AiiDA Calculations")
        monitor_layout = QVBoxLayout(group)
        
        # Calculations table
        self.aiida_table = QTableWidget()
        self.aiida_table.setColumnCount(5)
        self.aiida_table.setHorizontalHeaderLabels(['PK', 'Label', 'State', 'Created', 'Actions'])
        self.aiida_table.horizontalHeader().setStretchLastSection(True)
        monitor_layout.addWidget(self.aiida_table)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_aiida_calculations)
        monitor_layout.addWidget(refresh_btn)
        
        layout.addWidget(group)
        
        # Store reference for later visibility control
        self.aiida_monitor_group = group
        
        # Hide if AiiDA not available
        if not AIIDA_AVAILABLE:
            group.setVisible(False)
    
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
        
        # AiiDA menu (show even if not enabled, but disable actions)
        aiida_menu = menubar.addMenu("AiiDA")
        
        list_calcs_action = QAction("List Calculations", self)
        list_calcs_action.triggered.connect(self.show_aiida_calculations)
        list_calcs_action.setEnabled(self.aiida_enabled)
        aiida_menu.addAction(list_calcs_action)
        
        setup_action = QAction("Setup AiiDA", self)
        setup_action.triggered.connect(self.show_aiida_setup)
        aiida_menu.addAction(setup_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_connections(self):
        """Set up signal connections"""
        # AiiDA worker connections
        if self.aiida_enabled:
            self.aiida_worker.status_updated.connect(self.on_aiida_status_updated)
            self.aiida_worker.calculation_finished.connect(self.on_aiida_calculation_finished)
            self.aiida_worker.error_occurred.connect(self.on_aiida_error)
        
        # UI updates
        self.execution_mode.buttonClicked.connect(self.on_execution_mode_changed)
        self.workflow_combo.currentTextChanged.connect(self.update_analysis_tools)
    
    def on_execution_mode_changed(self, button):
        """Handle execution mode change"""
        is_aiida = self.execution_mode.checkedId() == 1
        
        # Show/hide AiiDA specific settings
        self.aiida_settings_group.setVisible(is_aiida)
        
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
            # AiiDA mode
            self.submit_to_aiida(config)
        else:
            # Local mode
            self.start_local_calculation(config)
    
    def submit_to_aiida(self, config):
        """Submit calculation to AiiDA"""
        try:
            inp_file = Path(config['inp_file'])
            op_file = Path(config['op_file'])
            workflow_type = config['workflow_type']
            
            db_folder = None
            if config.get('db_folder'):
                db_folder = Path(config['db_folder'])
            
            analysis_tools = config.get('analysis_tools', [])
            analysis_params = config.get('analysis_params', {})
            
            # Submit to AiiDA
            process_pk = self.aiida_worker.submit_calculation(
                inp_file, op_file, workflow_type, db_folder,
                bool(analysis_tools), analysis_params
            )
            
            if process_pk:
                self.append_log(f"Submitted calculation to AiiDA with PK: {process_pk}")
                self.aiida_calculations[str(process_pk)] = {
                    'label': config['calculation_name'],
                    'state': 'submitted',
                    'created': datetime.now().isoformat()
                }
                self.refresh_aiida_calculations()
            else:
                self.append_log("Failed to submit calculation to AiiDA")
                
        except Exception as e:
            self.append_log(f"Error submitting to AiiDA: {str(e)}")
    
    def start_local_calculation(self, config):
        """Start local calculation using the proven QuanticsRunner from quantics_gui_pyqt.py"""
        if not LOCAL_RUNNER_AVAILABLE:
            self.append_log("Error: QuanticsRunner from quantics_gui_pyqt.py not available")
            QMessageBox.critical(self, "Runner Error", 
                               "Cannot start local calculation: QuanticsRunner not available.\n"
                               "Please ensure quantics_gui_pyqt.py is accessible.")
            return
        
        # Create and start calculation thread using proven QuanticsRunner
        self.runner_thread = QuanticsRunner(config)
        
        # Connect signals for progress updates, logging, and completion
        self.runner_thread.progress_updated.connect(self.update_progress)
        self.runner_thread.log_updated.connect(self.append_log)
        self.runner_thread.calculation_finished.connect(self.on_local_calculation_finished)
        self.runner_thread.analysis_started.connect(self.on_analysis_started)
        self.runner_thread.analysis_finished.connect(self.on_analysis_finished)
        
        # Update UI state
        self.start_btn.setEnabled(False)
        if hasattr(self, 'stop_btn'):
            self.stop_btn.setEnabled(True)
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
        
        # Clear log and start
        self.append_log("=== Starting QUANTICS Calculation ===")
        self.append_log(f"Workflow type: {config['workflow_type']}")
        self.append_log(f"Calculation name: {config['calculation_name']}")
        
        # Start calculation
        self.runner_thread.start()
        if hasattr(self, 'status_label'):
            self.status_label.setText("Calculation in progress...")
    
    def on_aiida_status_updated(self, process_pk, status):
        """Handle AiiDA status updates"""
        if 'error' not in status:
            self.aiida_calculations[process_pk] = status
            self.refresh_aiida_calculations()
    
    def on_aiida_calculation_finished(self, process_pk, success, results):
        """Handle AiiDA calculation completion"""
        if success:
            self.append_log(f"AiiDA calculation {process_pk} completed successfully")
            # Display results
            self.display_aiida_results(process_pk, results)
        else:
            self.append_log(f"AiiDA calculation {process_pk} failed: {results.get('error', 'Unknown error')}")
    
    def on_aiida_error(self, error_msg):
        """Handle AiiDA errors"""
        self.append_log(f"AiiDA error: {error_msg}")
    
    def on_local_calculation_finished(self, success, result):
        """Callback when local calculation finishes (from QuanticsRunner)"""
        self.start_btn.setEnabled(True)
        if hasattr(self, 'stop_btn'):
            self.stop_btn.setEnabled(False)
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False)
        
        if success:
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"Calculation completed! Result: {result}")
            self.append_log("=== Calculation completed successfully ===")
            self.current_result_dir = result
            QMessageBox.information(self, "Calculation Complete", 
                                  f"Calculation completed successfully!\n\nResults directory: {result}")
            self.load_results(result)
        else:
            if hasattr(self, 'status_label'):
                self.status_label.setText("Calculation failed")
            self.append_log(f"=== Calculation failed: {result} ===")
            QMessageBox.critical(self, "Calculation Failed", 
                               f"Error occurred during calculation:\n\n{result}")
    
    def on_analysis_started(self, tool):
        """Callback when analysis starts (from QuanticsRunner)"""
        self.append_log(f"Starting analysis: {tool}")
    
    def on_analysis_finished(self, tool, success):
        """Callback when analysis finishes (from QuanticsRunner)"""
        status = "Success" if success else "Failed"
        self.append_log(f"Analysis {tool} {status}")
    
    def update_progress(self, value):
        """Update progress bar (from QuanticsRunner)"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(value)
    
    def load_results(self, result_dir):
        """Load results to tree view"""
        if hasattr(self, 'result_tree'):
            self.result_tree.clear()
            
            if not os.path.exists(result_dir):
                return
                
            root_item = QTreeWidgetItem(self.result_tree)
            root_item.setText(0, os.path.basename(result_dir))
            root_item.setText(1, "Directory")
            
            self.populate_tree(root_item, result_dir)
            self.result_tree.expandAll()
            self.result_tree.resizeColumnToContents(0)
    
    def populate_tree(self, parent_item, dir_path):
        """Recursively populate tree view"""
        try:
            for item in sorted(os.listdir(dir_path)):
                item_path = os.path.join(dir_path, item)
                tree_item = QTreeWidgetItem(parent_item)
                
                if os.path.isdir(item_path):
                    tree_item.setText(0, f"[DIR] {item}")
                    tree_item.setText(1, "Directory")
                    self.populate_tree(tree_item, item_path)
                else:
                    # File icon based on extension
                    ext = os.path.splitext(item)[1].lower()
                    if ext in ['.dat', '.txt']:
                        icon = "[TXT]"
                    elif ext in ['.log']:
                        icon = "[LOG]"  
                    elif ext in ['.out']:
                        icon = "[OUT]"
                    else:
                        icon = "[FILE]"
                    
                    tree_item.setText(0, f"{icon} {item}")
                    
                    # File size
                    size = os.path.getsize(item_path)
                    if size > 1024*1024:
                        size_str = f"{size/(1024*1024):.1f} MB"
                    elif size > 1024:
                        size_str = f"{size/1024:.1f} KB"
                    else:
                        size_str = f"{size} B"
                    tree_item.setText(1, size_str)
                    
                    # Modification time
                    mtime = os.path.getmtime(item_path)
                    mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                    tree_item.setText(2, mtime_str)
        except PermissionError:
            pass
    
    def refresh_aiida_calculations(self):
        """Refresh AiiDA calculations table"""
        if not self.aiida_enabled:
            return
        
        self.aiida_table.setRowCount(len(self.aiida_calculations))
        
        for row, (pk, calc_info) in enumerate(self.aiida_calculations.items()):
            self.aiida_table.setItem(row, 0, QTableWidgetItem(pk))
            self.aiida_table.setItem(row, 1, QTableWidgetItem(calc_info.get('label', '')))
            self.aiida_table.setItem(row, 2, QTableWidgetItem(calc_info.get('state', '')))
            self.aiida_table.setItem(row, 3, QTableWidgetItem(calc_info.get('created', '')))
            
            # Actions button
            actions_btn = QPushButton("View")
            actions_btn.clicked.connect(lambda checked, p=pk: self.view_aiida_calculation(p))
            self.aiida_table.setCellWidget(row, 4, actions_btn)
    
    def view_aiida_calculation(self, process_pk):
        """View AiiDA calculation details"""
        # Implement calculation details viewer
        self.append_log(f"Viewing calculation {process_pk}")
    
    def display_aiida_results(self, process_pk, results):
        """Display AiiDA calculation results"""
        self.append_log(f"Results for calculation {process_pk}:")
        if 'calculation' in results:
            calc_results = results['calculation']
            for key, value in calc_results.items():
                self.append_log(f"  {key}: {value}")
        
        if 'analysis' in results:
            self.append_log("Analysis results:")
            analysis_results = results['analysis']
            for tool, output in analysis_results.items():
                self.append_log(f"  {tool}: Available")
    
    # Include all the existing methods from the original GUI
    def update_analysis_tools(self, workflow_type):
        """Update analysis tools based on workflow type (from quantics_gui_pyqt.py)"""
        self.analysis_list.clear()
        
        if workflow_type in self.workflow_analysis_map:
            tools = self.workflow_analysis_map[workflow_type]
            for tool, description in tools:
                item = QListWidgetItem(f"{tool} - {description}")
                self.analysis_list.addItem(item)
        
        # Highlight DB folder for DD-vMCG
        if workflow_type == 'DD-vMCG':
            self.db_folder_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            self.db_folder_edit.setStyleSheet("QLineEdit { border: 2px solid red; }")
        else:
            self.db_folder_label.setStyleSheet("")
            self.db_folder_edit.setStyleSheet("")
    
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
        
        if self.workflow_combo.currentText() == 'DD-vMCG':
            if not self.db_folder_edit.text() or not Path(self.db_folder_edit.text()).exists():
                QMessageBox.warning(self, "Folder Error", "DD-vMCG workflow requires a valid DB folder")
                return False
        
        return True
    
    def collect_config(self):
        """Collect configuration from UI"""
        selected_tools = []
        for i in range(self.analysis_list.count()):
            item = self.analysis_list.item(i)
            if item.isSelected():
                tool_cmd = item.text().split(' - ')[0]
                selected_tools.append(tool_cmd)
        
        config = {
            'calculation_name': self.calc_name_edit.text(),
            'workflow_type': self.workflow_combo.currentText(),
            'inp_file': self.inp_file_edit.text(),
            'op_file': self.op_file_edit.text(),
            'db_folder': self.db_folder_edit.text() if self.db_folder_edit.text() else None,
            'quantics_executable': self.quantics_exec_edit.text(),
            'working_directory': self.work_dir_edit.text() if self.work_dir_edit.text() else None,
            'analysis_tools': selected_tools,
            'save_inputs': self.save_inputs_cb.isChecked(),
            'cleanup_on_success': self.cleanup_cb.isChecked(),
            # Analysis tool parameters
            'rdgpop_nz': self.rdgpop_nz_edit.text().strip() or "2",
            'rdgpop_dof': self.rdgpop_dof_edit.text().strip() or "1",
            'show_cmdline': self.show_cmdline_cb.isChecked()
        }
        
        # AiiDA specific settings
        if self.execution_mode.checkedId() == 1:
            config['aiida_resources'] = int(self.resources_edit.text() or 1)
            config['aiida_walltime'] = int(self.walltime_edit.text() or 3600)
            config['aiida_queue'] = self.queue_edit.text() or None
        
        return config
    
    def append_log(self, message):
        """Append message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.ensureCursorVisible()
    
    # Add other existing methods...
    def select_all_analysis(self):
        """Select all analysis tools"""
        for i in range(self.analysis_list.count()):
            self.analysis_list.item(i).setSelected(True)
    
    def select_none_analysis(self):
        """Deselect all analysis tools"""
        self.analysis_list.clearSelection()
    
    def preview_analysis_params(self):
        """Preview analysis parameters"""
        # Get selected analysis tools
        selected_tools = []
        for i in range(self.analysis_list.count()):
            item = self.analysis_list.item(i)
            if item.isSelected():
                tool_cmd = item.text().split(' - ')[0]
                selected_tools.append(tool_cmd)
        
        if not selected_tools:
            QMessageBox.information(self, "Parameters Preview", "No analysis tools selected.")
            return
        
        # Create preview text
        preview_text = "Analysis Tools Configuration:\n\n"
        
        for tool in selected_tools:
            preview_text += f"• {tool}\n"
            if tool == "rdgpop":
                nz = self.rdgpop_nz_edit.text() or "2"
                dof = self.rdgpop_dof_edit.text() or "1"
                preview_text += f"   Command: rdgpop -w\n"
                preview_text += f"   Parameters: nz={nz}, dof={dof}\n"
                preview_text += f"   Effect: Sum {nz} grid points for DOF {dof}\n"
            elif tool.startswith("rdcheck"):
                preview_text += f"   Command: {tool}\n"
                if "natpop" in tool:
                    preview_text += f"   Effect: Check natural populations\n"
                elif "etot" in tool:
                    preview_text += f"   Effect: Check energy conservation\n"
                elif "spop" in tool:
                    preview_text += f"   Effect: Check single particle populations\n"
            elif tool == "ddtraj":
                preview_text += f"   Command: ddtraj\n"
                preview_text += f"   Effect: Direct dynamics trajectory analysis\n"
            preview_text += "\n"
        
        if self.show_cmdline_cb.isChecked():
            preview_text += "Note: Command line output will be displayed in log.\n"
        
        QMessageBox.information(self, "Parameters Preview", preview_text)
    
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
    
    def check_calculation_name(self):
        """Check calculation name validity"""
        name = self.calc_name_edit.text()
        if name and not name.replace('_', '').replace('-', '').isalnum():
            self.calc_name_edit.setStyleSheet("QLineEdit { border: 2px solid red; }")
        else:
            self.calc_name_edit.setStyleSheet("")
    
    def new_calculation(self):
        """Start new calculation"""
        reply = QMessageBox.question(self, "New Calculation", "Clear current configuration?")
        if reply == QMessageBox.Yes:
            # Reset all fields
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
            self, "Save Configuration", 
            f"quantics_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
            "JSON files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=2)
                QMessageBox.information(self, "Save Successful", f"Configuration saved to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Failed", f"Error saving configuration: {str(e)}")
    
    def load_config(self):
        """Load configuration"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", "", "JSON files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                
                # Apply configuration
                self.calc_name_edit.setText(config.get('calculation_name', ''))
                self.workflow_combo.setCurrentText(config.get('workflow_type', 'MCTDH'))
                self.inp_file_edit.setText(config.get('inp_file', ''))
                self.op_file_edit.setText(config.get('op_file', ''))
                self.db_folder_edit.setText(config.get('db_folder', '') or '')
                self.quantics_exec_edit.setText(config.get('quantics_executable', 'quantics'))
                self.work_dir_edit.setText(config.get('working_directory', '') or '')
                self.save_inputs_cb.setChecked(config.get('save_inputs', True))
                self.cleanup_cb.setChecked(config.get('cleanup_on_success', False))
                
                # Load analysis parameters
                self.rdgpop_nz_edit.setText(config.get('rdgpop_nz', '2'))
                self.rdgpop_dof_edit.setText(config.get('rdgpop_dof', '1'))
                self.show_cmdline_cb.setChecked(config.get('show_cmdline', True))
                
                QMessageBox.information(self, "Load Successful", f"Configuration loaded from {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Load Failed", f"Error loading configuration: {str(e)}")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About QUANTICS GUI with AiiDA", 
                         f"""
                         <h2>QUANTICS Professional GUI with AiiDA Integration</h2>
                         <p><b>Version:</b> 3.0.0</p>
                         <p><b>Advanced quantum dynamics calculation interface</b></p>
                         
                         <h3>Features:</h3>
                         <ul>
                         <li>Local and distributed execution</li>
                         <li>AiiDA workflow management</li>
                         <li>Data provenance tracking</li>
                         <li>High-throughput calculations</li>
                         <li>Dynamic analysis tools</li>
                         </ul>
                         
                         <p><b>AiiDA Status:</b> {'Enabled' if self.aiida_enabled else 'Not Available'}</p>
                         """)
    
    def save_log(self):
        """Save log to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Log", f"quantics_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 
            "Text files (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "Save Successful", f"Log saved to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Failed", f"Error saving log: {str(e)}")
    
    def refresh_results(self):
        """Refresh results display"""
        if self.current_result_dir:
            self.load_results(self.current_result_dir)
    
    def open_result_directory(self):
        """Open results directory"""
        if self.current_result_dir and os.path.exists(self.current_result_dir):
            if sys.platform.startswith('win'):
                os.startfile(self.current_result_dir)
            elif sys.platform.startswith('darwin'):
                subprocess.run(['open', self.current_result_dir])
            else:
                subprocess.run(['xdg-open', self.current_result_dir])
    
    def stop_calculation(self):
        """Stop calculation"""
        if self.runner_thread and self.runner_thread.isRunning():
            self.runner_thread.terminate()
            self.runner_thread.wait()
            
        self.start_btn.setEnabled(True)
        if hasattr(self, 'stop_btn'):
            self.stop_btn.setEnabled(False)
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False)
        if hasattr(self, 'status_label'):
            self.status_label.setText("Calculation stopped")
        self.append_log("Calculation stopped by user")
    
    def show_aiida_calculations(self):
        """Show AiiDA calculations browser"""
        # Implement AiiDA calculations browser
        QMessageBox.information(self, "AiiDA", "AiiDA calculations browser will be implemented here")
    
    def show_aiida_setup(self):
        """Show AiiDA setup dialog"""
        # Implement AiiDA setup dialog
        QMessageBox.information(self, "AiiDA Setup", "AiiDA setup dialog will be implemented here")
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.aiida_enabled:
            self.aiida_worker.stop_monitoring()
            self.aiida_worker.wait()
        event.accept()


def main():
    """Main function"""
    if not QT_AVAILABLE:
        print("Error: PyQt5 or PySide2 required for GUI")
        return
    
    app = QApplication(sys.argv)
    
    # Set application information
    app.setApplicationName("QUANTICS Professional GUI with AiiDA")
    app.setApplicationVersion("3.0.0")
    app.setOrganizationName("Quantics Team")
    
    # Create main window
    window = QuanticsAiidaMainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 