# QUANTICS-AiiDA Complete Installation and Usage Guide

## Overview

This guide will help you install and configure the entire QUANTICS-AiiDA system from scratch, including:
- AiiDA installation and configuration
- Hartree cluster connection setup
- QUANTICS software configuration
- GUI interface usage

**Target Audience:** Complete beginners who have never used AiiDA and QUANTICS before

---

## Part 1: Environment Preparation

### 1.1 System Requirements

- **Operating System:** 
  - Native Linux Ubuntu 22.04 or higher (recommended)
  - OR WSL2 (Windows Subsystem for Linux) Ubuntu 22.04 on Windows
- **Python:** 3.8 or higher
- **Network:** Ability to connect to hartree.chem.ucl.ac.uk

**Note:** WSL2 is a Linux virtual environment running on Windows. If you're using Windows, you can install WSL2 to run Linux commands. If you're already on a native Linux system, you can skip WSL2-specific configurations.

### 1.2 Check Python Environment

```bash
python3 --version
pip3 --version
```

If Python is not installed, install it:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

---

## Part 2: AiiDA Installation and Configuration

### 2.1 Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv aiida_env

# Activate virtual environment
source aiida_env/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 2.2 Install AiiDA

```bash
# Install AiiDA core package
pip install aiida-core[atomic_tools]==2.6.2

# Install PostgreSQL related packages (AiiDA database)
pip install psycopg2-binary

# Install SGE scheduler plugin
pip install aiida-sge

# Install other required packages
pip install paramiko click-completion
```

### 2.3 Install and Configure PostgreSQL Database

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database user
sudo -u postgres createuser -P aiida
# When prompted for password, use a simple password like: aiida123

# Create database
sudo -u postgres createdb -O aiida aiida_db
```

### 2.4 Initialize AiiDA

```bash
# Initialize AiiDA (first run)
verdi quicksetup

# Enter when prompted:
# Profile name: your.email like UCL ID
# Email: your.email(profile name)@ucl.ac.uk
# First name: Your Name
# Last name: Your Last Name
# Institution: UCL
# Database backend: postgresql_psycopg2
# PostgreSQL hostname: localhost
# PostgreSQL port: 5432
# PostgreSQL database name: aiida_db
# PostgreSQL username: aiida
# PostgreSQL password: aiida123

# Verify installation
verdi status
```

### 2.5 Start AiiDA Daemon

```bash
# Start daemon
verdi daemon start

# Check status
verdi daemon status
```

---

## Part 3: Hartree Cluster Configuration

### 3.1 Set up SSH Keys (if not already done)

```bash
# Generate SSH key pair
ssh-keygen -t rsa -b 4096

# Copy public key to hartree cluster
ssh-copy-id your_username@hartree.chem.ucl.ac.uk

# Test connection
ssh your_username@hartree.chem.ucl.ac.uk
```

### 3.2 Configure AiiDA Computer

```bash
# Set up computer
verdi computer setup

# Enter when prompted:
# Computer label: hartree
# Hostname: hartree.chem.ucl.ac.uk
# Description: Hartree cluster at UCL
# Transport plugin: core.ssh
# Scheduler plugin: core.sge
# Work directory: /home/your_username/aiida_work
# Mpirun command: mpirun -np {tot_num_mpiprocs}
# Default number of CPUs per machine: 1

# Configure SSH connection
verdi computer configure core.ssh hartree

# Enter when prompted:
# Username: your_username
# Port: 22
# Look for keys: True
# SSH key file: /home/your_local_username/.ssh/id_rsa
# SSH key passphrase: (if you have a passphrase)
# Connection timeout: 60
# Allow agent: True
# SSH proxy jump: (leave empty)
# SSH proxy command: (leave empty)
# Compress: True
# GSS auth: False
# GSS kex: False
# GSS deleg_creds: False
# GSS host: hartree.chem.ucl.ac.uk
# Load system host keys: True
# Key policy: RejectPolicy

# Test connection
verdi computer test hartree
```

### 3.3 Verify Computer Configuration

After configuring the computer, run these verification commands:

```bash
# Test the computer connection
verdi computer test hartree

# Show detailed computer information
verdi computer show hartree

# List all configured computers
verdi computer list
```

Expected output from `verdi computer list` should show:
```
Report: List of configured computers
Report: Use 'verdi computer show COMPUTERLABEL' to display more detailed information
* hartree
* hartree-clean
* localhost
```

Check AiiDA process status:
```bash
# List all processes (jobs)
verdi process list -a
```

**Additional Connection Test:**
Test direct SSH connection to ensure network connectivity:
```bash
# Test SSH connection and file access (replace ucapjd1 with your username)
ssh ucapjd1@hartree.chem.ucl.ac.uk ls -l ~/aiida_run/test_upload.txt
```

This command verifies:
- SSH connection is working
- Your credentials are correct
- You can access the hartree filesystem

### 3.4 Configure QUANTICS Code

```bash
# Set up QUANTICS code
verdi code create core.code.installed

# Enter when prompted:
# Label: quantics-hartree
# Computer: hartree
# Default calculation input plugin: (leave empty)
# Absolute path of executable: /home/agiussani/quantics-6-6-16/bin/binary/x86_64/quantics
# List of prepend text: (leave empty)
# List of append text: (leave empty)

# Verify code setup
verdi code list
verdi code show quantics-hartree@hartree
```

---

## Part 4: Install GUI Interface Dependencies

### 4.1 Install PyQt5 and Other GUI Dependencies

```bash
# Make sure you're in the aiida virtual environment
source aiida_env/bin/activate

# Install PyQt5
pip install PyQt5

# If using WSL2, install X11 support
sudo apt install python3-pyqt5 python3-pyqt5.qtwidgets
```

### 4.2 Graphical Interface Configuration

#### For Native Linux Systems:
Most Linux distributions have built-in X11 support. No additional configuration needed.

#### For WSL1 (Windows Subsystem for Linux Version 1):

**Step 1: Install X Server on Windows**

1. Download and install VcXsrv (free and open source):
   - Official download link: https://sourceforge.net/projects/vcxsrv/

2. Launch VcXsrv with the following settings:
   - Select "Multiple windows"
   - Select "Start no client"
   - In "Extra settings", check "Disable access control" (this allows WSL1 to connect directly)
   - Click "Finish"
   - VcXsrv icon will appear in system tray, indicating the server is listening on 0.0.0.0:6000

**Step 2: Configure DISPLAY Environment Variable in WSL1**

Open your WSL1 terminal and edit `~/.bashrc`:
```bash
# Add X server address (localhost for WSL1)
echo 'export DISPLAY=localhost:0.0' >> ~/.bashrc
echo 'export LIBGL_ALWAYS_INDIRECT=1' >> ~/.bashrc

# Apply changes
source ~/.bashrc
```

**Step 3: Test X11 Connection**

Install and test X11 applications:
```bash
# Update package list
sudo apt update

# Install X11 test applications
sudo apt install x11-apps -y

# Test X11 forwarding
xeyes
```

If you see two small eyes following your mouse on the Windows desktop, X11 forwarding is working correctly.

**Troubleshooting for WSL1:**

If `xeyes` shows "Error: Can't open display:", manually set the environment variables in the current session:
```bash
export DISPLAY=localhost:0.0
export LIBGL_ALWAYS_INDIRECT=1
xeyes
```

**Windows Firewall Configuration:**
- Open "Windows Security" → "Firewall & network protection" → "Advanced settings" → "Inbound Rules"
- Create or find a rule allowing TCP port 6000 inbound connections for "Any" or "vEthernet (WSL)" network

#### For WSL2 (Windows Subsystem for Linux Version 2):
```bash
# Install X11 server support
sudo apt install x11-apps

# Set DISPLAY variable in WSL2
echo 'export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk "{print \$2}"):0.0' >> ~/.bashrc
source ~/.bashrc
```

**Note for WSL2 users:** You need to install an X11 server on Windows (such as VcXsrv or X410) to display GUI applications.

#### Alternative for Windows 11: WSLg
If you're using Windows 11 with the latest WSL version that includes WSLg:
```powershell
# Update WSL to enable WSLg
wsl --update
```
With WSLg, GUI applications run directly without additional X server installation.

---

## Part 5: Get and Configure QUANTICS GUI

### 5.1 Get GUI Files

Make sure you have the following files in your working directory:
- `quantics_gui_aiida.py` - QUANTICS Professional GUI (supports both local and AiiDA modes)
- `quantics_aiida_integration.py` - AiiDA integration module
- `quantics_local_runner.py` - Local execution module

**Note:** We use an integrated GUI version that supports both local execution and AiiDA cluster execution modes.

### 5.2 Test AiiDA Configuration

```bash
# Run test in GUI directory
python3 -c "
from quantics_aiida_integration import QuanticsAiidaIntegration
integration = QuanticsAiidaIntegration()
print('AiiDA Configuration Test:', integration.test_aiida_setup())
"
```

---

## Part 6: Using the GUI Interface

### 6.1 Start QUANTICS Professional GUI

```bash
# Activate virtual environment
source aiida_env/bin/activate

# Make sure AiiDA daemon is running (if using AiiDA mode)
verdi daemon status

# Start QUANTICS Professional GUI
python3 quantics_gui_aiida.py
```

### 6.2 Choose Execution Mode

After starting the GUI, you can choose between two execution modes:

**Local Execution Mode:**
- Suitable for quick testing and small-scale calculations
- Calculations run on local machine
- No cluster connection required

**AiiDA Workflow Mode:**
- Suitable for large-scale calculations and production tasks
- Calculations submitted to hartree cluster
- Supports workflow management and data provenance

---

## Part 7: GUI Interface Usage Instructions

### 7.1 QUANTICS Professional GUI Interface Features

#### Main Components:
1. **Execution Mode Selection** - Choose between local execution and AiiDA workflow
2. **Configuration Panel** - Set input files, workflow type, and run parameters
3. **Analysis Tools Panel** - Select post-processing analysis tools
4. **Calculation Log Panel** - Display real-time calculation logs
5. **AiiDA Monitor Panel** - Monitor AiiDA job status (AiiDA mode only)
6. **Results Browser Panel** - View calculation results and output files

#### Basic Usage Workflow:

**Step 1: Choose Execution Mode**
1. Select "Local Execution" for quick testing and small calculations
2. Select "AiiDA Workflow" for cluster calculations

**Step 2: Configure Basic Settings**
1. **Calculation Name:** Give your calculation task a meaningful name
2. **Workflow Type:** Choose MCTDH, vMCG, or DD-vMCG
3. **QUANTICS Executable:** Usually defaults to "quantics"
4. **Working Directory:** Optional, specify calculation run directory

**Step 3: Select Input Files**
1. Click "Browse" button for ".inp file" to select QUANTICS input file
2. Click "Browse" button for ".op file" to select operator file
3. If using DD-vMCG workflow, also select "DB folder" (database folder)

**Step 4: Configure Analysis Tools (Optional)**
1. In "Post-processing Analysis" panel, select required analysis tools:
   - `rdcheck etot` - Check total energy
   - `rdcheck spop` - Check single particle population
   - `rdcheck natpop` - Check natural population
   - `rdgpop` - Grid population analysis
2. For `rdgpop` tool, you can set:
   - **nz value:** Number of grid points (default: 2)
   - **dof value:** Degree of freedom number (default: 1)
   - **Show command line:** Whether to show detailed commands

**Step 5: Submit Calculation**
1. Check all parameter settings
2. Click "Start Calculation" (local mode) or "Submit to AiiDA" (AiiDA mode)
3. Calculation starts running or gets submitted to cluster

**Step 6: Monitor Calculation Status**
- **Local Mode:** View real-time output in log panel, progress bar shows calculation progress
- **AiiDA Mode:** Monitor job status in AiiDA monitor panel, including CREATED, SUBMITTED, RUNNING, FINISHED states

**Step 7: View Results**
1. After calculation completion, view output files in "Results Browser" panel
2. Open result directory to view all output files
3. View analysis tool results (if analysis tools were used)

### 7.2 Common Operations

#### Local Mode Operations
```
- Stop calculation: Click "Stop Calculation" button
- Clear log: Click "Clear Log" button
- Save log: Click "Save Log" button
- Refresh results: Click "Refresh" button to update results display
- Open result directory: Click "Open Directory" button
```

#### AiiDA Mode Operations
```
- Refresh job list: Click "Refresh" button to update AiiDA job status
- View job details: Click "View" button in job row
- Monitor job status: View job progress in AiiDA monitor panel
```

#### Configuration Operations
```
- Save configuration: Menu → File → Save Configuration
- Load configuration: Menu → File → Load Configuration
- New calculation: Menu → File → New Calculation
```

---

## Part 8: Troubleshooting

### 8.1 Common Issues

**Issue 1: AiiDA daemon cannot start**
```bash
# Solution
verdi daemon stop
verdi daemon start
```

**Issue 2: Cannot connect to hartree cluster**
```bash
# Test SSH connection
ssh your_username@hartree.chem.ucl.ac.uk

# Reconfigure computer
verdi computer configure core.ssh hartree
```

**Issue 3: GUI cannot start**

For Native Linux:
```bash
# Check if X11 is running
echo $DISPLAY
xeyes  # Test graphical interface

# If DISPLAY is empty, try:
export DISPLAY=:0.0
```

For WSL2:
```bash
# Check X11 forwarding
echo $DISPLAY
xeyes  # Test graphical interface

# Reset DISPLAY variable for WSL2
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0
```

**Issue 4: Job submission fails**
```bash
# Check AiiDA status
verdi status

# View daemon logs
verdi daemon logshow
```

### 8.2 Log File Locations

- **AiiDA logs:** `~/.aiida/daemon/log/`
- **Job logs:** View through GUI's "Show Results"
- **System logs:** `/var/log/`

---

## Part 9: Advanced Configuration

### 9.1 Performance Optimization

```bash
# Increase daemon worker processes
verdi daemon incr 4

# Set larger work directory
verdi computer configure core.ssh hartree
# Modify Work directory to larger storage space
```

### 9.2 Custom Analysis Tools

You can add new analysis tools in `quantics_gui_aiida.py`. Find the `workflow_analysis_map` dictionary and add new tools:

```python
# Add new tool in workflow_analysis_map dictionary for specific workflows
self.workflow_analysis_map = {
    'MCTDH': [
        ('rdcheck etot', 'Total energy check'),
        ('rdcheck spop', 'Single particle population'),
        ('rdcheck natpop 0 0', 'Natural potential analysis'),
        ('rdgpop', 'Grid population analysis'),
        ('your_new_tool', 'Your tool description')  # Add new tool
    ],
    # ... other workflow types
}
```

---

## Part 10: Maintenance and Backup

### 10.1 Database Backup

```bash
# Export AiiDA database
verdi archive create backup.aiida

# Restore database
verdi archive import backup.aiida
```

### 10.2 Regular Maintenance

```bash
# Clean old job data
verdi calcjob cleanworkdir --older-than 30  # Clean work directories older than 30 days

# Check system status
verdi status
verdi daemon status
```

---

## Quick Start Checklist

Before using, make sure all the following items are completed:

- [ ] PostgreSQL database running normally
- [ ] AiiDA profile configured (`verdi status` shows green)
- [ ] AiiDA daemon running (`verdi daemon status` shows running)
- [ ] Hartree cluster SSH connection working (`verdi computer test hartree` succeeds)
- [ ] QUANTICS code path correctly configured
- [ ] Virtual environment activated
- [ ] GUI dependencies installed (PyQt5)
- [ ] X11 forwarding set up correctly (if using WSL2) or X11 working (native Linux)

---

## Quick Start Commands

Use the following commands to quickly start QUANTICS Professional GUI:

```bash
# Go to project directory
cd ~/quantics_exercises/test

# Activate environment and start GUI
source quantics_env.sh && python quantics_gui_aiida.py
```

This command will:
1. Activate virtual environment
2. Set QUANTICS environment variables
3. Start the professional GUI interface

---

## Technical Support

If you encounter problems, please check:
1. System logs and error messages
2. AiiDA official documentation: https://aiida.readthedocs.io/
3. QUANTICS user manual
4. Contact system administrator or development team

---