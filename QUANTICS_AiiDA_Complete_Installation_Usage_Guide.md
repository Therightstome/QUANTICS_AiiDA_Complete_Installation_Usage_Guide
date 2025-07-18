# QUANTICS-AiiDA Complete Installation and Usage Guide

## Overview

This guide will help you install and configure the entire QUANTICS-AiiDA system from scratch, including:
- AiiDA installation and configuration
- RabbitMQ message broker configuration
- QUANTICS software local installation
- Hartree cluster connection setup
- QUANTICS software configuration
- GUI interface usage

**Target Audience:** Complete beginners who have never used AiiDA and QUANTICS before

**AiiDA Version:** This guide is compatible with AiiDA 2.7.0 and later versions, including the latest profile setup commands and storage plugin configurations.

---

## Part 1: Environment Preparation

### 1.1 System Requirements

- **Operating System:** Linux/WSL2 Ubuntu 22.04 or higher
- **Python:** 3.8 or higher
- **Network:** Ability to connect to hartree.chem.ucl.ac.uk

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

## Part 2: RabbitMQ Installation (Optional but Recommended)

### 2.1 Why RabbitMQ is Needed

RabbitMQ is a message broker that, while optional, is **strongly recommended** for installation. It enables AiiDA's daemon to:
- Run multiple computation tasks in parallel
- Manage task queues in the background
- Provide better performance and scalability

### 2.2 Install RabbitMQ

```bash
# Ubuntu/Debian systems
sudo apt install rabbitmq-server
```

#### Starting RabbitMQ Service

**For native Linux systems (systemd support):**
```bash
# Start RabbitMQ service
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server

# Verify RabbitMQ status
sudo systemctl status rabbitmq-server
```

**For WSL1/WSL2 or systems without systemd:**
```bash
# Start RabbitMQ service manually
sudo service rabbitmq-server start

# Or directly start RabbitMQ
sudo rabbitmq-server -detached

# Verify RabbitMQ status
sudo rabbitmqctl status

# Enable auto-start (optional)
sudo update-rc.d rabbitmq-server enable
```

#### Verify RabbitMQ Installation
```bash
# Check if RabbitMQ is running
sudo rabbitmqctl status

# If you see output similar to the following, RabbitMQ is running:
# Status of node rabbit@hostname...
# Runtime
# [{pid,12345}]
```

---

## Part 3: AiiDA Installation and Configuration

### 3.1 Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv aiida_env

# Activate virtual environment
source aiida_env/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 3.2 Install AiiDA

```bash
# Install AiiDA core package (latest version recommended)
pip install aiida-core[atomic_tools]

# Install PostgreSQL related packages (AiiDA database)
pip install psycopg2-binary

# Install other required packages
pip install paramiko click-completion
```

### 3.3 Install and Configure PostgreSQL Database

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib
```

#### Start PostgreSQL Service

**For native Linux systems (systemd support):**
```bash
# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**For WSL1/WSL2 or systems without systemd:**
```bash
# Start PostgreSQL service manually
sudo service postgresql start

# Verify PostgreSQL is running
sudo service postgresql status

# Or check PostgreSQL processes
ps aux | grep postgres
```

#### Configure PostgreSQL Database

**Method 1: Using PostgreSQL command line tools**
```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Execute the following commands in psql:
CREATE USER aiida WITH PASSWORD 'aiida123';
CREATE DATABASE aiida_db OWNER aiida ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';
GRANT ALL PRIVILEGES ON DATABASE aiida_db TO aiida;
\q
```

**Method 2: Using system commands (simpler)**
```bash
# Create user
sudo -u postgres createuser -P aiida
# When prompted for password, use a simple password like: aiida123

# Create database
sudo -u postgres createdb -O aiida aiida_db
```

#### Test Database Connection
```bash
# Test database connection
psql -h localhost -d aiida_db -U aiida -W
# Enter password aiida123, successful connection means correct configuration
```

### 3.4 Initialize AiiDA

#### Storage Plugin Selection Guide

AiiDA 2.7.0 supports multiple storage plugins:
- **core.psql_dos** - Uses PostgreSQL + disk-objectstore, suitable for production environments, best performance
- **core.sqlite_dos** - Uses SQLite + disk-objectstore, suitable for testing and learning, no additional services required

**For QUANTICS workloads, core.psql_dos plugin is strongly recommended for best performance.**

#### Method 1: Manual Configuration (Recommended for Learning)

```bash
# Create AiiDA profile (using PostgreSQL storage)
verdi profile setup core.psql_dos

# Enter when prompted:
# Profile name: your.email like UCL ID
# Email: your.email@ucl.ac.uk
# First name: Your Name
# Last name: Your Last Name
# Institution: UCL
# Database hostname: localhost
# Database port: 5432
# Database name: aiida_db
# Database username: aiida
# Database password: aiida123
# Use RabbitMQ broker: y (recommended to choose yes)

# Verify installation
verdi status
```

#### Method 2: Automated Configuration (Quick Setup)

```bash
# Use verdi presto for automated configuration (AiiDA 2.7.0+ new feature)
verdi presto --use-postgres

# This command will automatically:
# 1. Create PostgreSQL database and user
# 2. Set up AiiDA profile
# 3. Configure RabbitMQ (if available)
# 4. Start daemon

# Verify installation
verdi status
```

**Note:** If Method 2 encounters permission issues, manually create the database user first (refer to Section 3.3), then use Method 1 for manual configuration.

### 3.5 Start AiiDA Daemon

```bash
# Start daemon
verdi daemon start

# Check status
verdi daemon status
```

---

## Part 4: QUANTICS Software Installation

### 4.1 QUANTICS Installation Overview

Before configuring AiiDA connection to the hartree cluster, it's important to understand the QUANTICS software installation process. While in actual AiiDA workflows, QUANTICS will run on remote compute nodes, understanding its installation process helps with:

1. **Understanding software dependencies**
2. **Local testing and development**
3. **Troubleshooting and debugging**
4. **Preparing for custom computational environments**

**Important Reminder:** Before proceeding, please visit the following official resources for detailed understanding:
- **Official Installation Documentation:** https://www2.chem.ucl.ac.uk/quantics/quantics2.1/doc/quantics/gen.html
- **Source Code Repository:** https://gitlab.com/quantics/quantics

**Please carefully read the above official documentation first to understand QUANTICS basic concepts, installation requirements, and usage methods before continuing with the installation steps.**

### 4.2 QUANTICS Software Overview

QUANTICS is a suite of programs capable of setting up and propagating wavepackets using various methods such as MCTDH. It can perform:
- Numerically exact propagation (small systems)
- Time-independent Schrödinger equation solutions
- Ground state wavefunction generation
- Excited state calculations
- Density operator propagation
- Multi-dimensional potential energy surface fitting (POTFIT)

### 4.3 Local QUANTICS Installation

If you wish to install QUANTICS in your local environment for testing or development, follow these steps:

#### Step 1. Install Dependencies

```bash
sudo apt update
sudo apt install gfortran gcc g++ make bash sqlite3 libsqlite3-dev \
                 texlive-latex-base texlive-fonts-recommended texlive-latex-extra \
                 dvipng evince gnuplot git mpich curl unzip
```

#### Step 2. Clone QUANTICS Source Code (Development Branch Recommended)

```bash
cd ~
git clone https://gitlab.com/quantics/quantics.git quantics --recursive
cd quantics
```

If you prefer the stable version, use:
```bash
git checkout master
```

#### Step 3. Auto-install QUANTICS Main Program

```bash
cd install
./install_quantics
```

The process will prompt for compilation, documentation, and variable settings—generally select default by pressing Enter.

#### Step 4. Set Environment Variables (Persistent)

You need to add the following content to `.bashrc` (once only):

```bash
echo 'export QUANTICS_DIR=~/quantics' >> ~/.bashrc
echo 'source $QUANTICS_DIR/install/QUANTICS_client' >> ~/.bashrc
source ~/.bashrc
```

#### Step 5. Verify Installation Success

```bash
quantics -h      # Output help information indicates success
menv             # Check if environment variables are loaded
```

#### Step 6. Compile Parallel Versions (Optional)

**OpenMP Parallel Version (Multi-threaded)**
```bash
compile -O quantics
quantics.omp -omp 4 input
```

**MPI Parallel Version (Multi-process)**
```bash
compile -m quantics
mpirun -np 4 quantics.mpi -mpi input
```

### 4.4 QUANTICS System Requirements

According to the official documentation, QUANTICS requires the following software environment:

- **Operating System:** UNIX or UNIX-like systems (Linux recommended)
- **FORTRAN Compiler:** GFORTRAN (version 8 or below recommended)
- **C Compiler:** C compiler compatible with FORTRAN compiler
- **SQLite Support:** gfortran requires sqlite3 and sqlite3-devel packages
- **Bash Shell:** Version 2.0 recommended, 1.14 also works
- **LaTeX:** For compiling documentation
- **GNUPLOT:** Version 5.0 or above
- **WWW Browser:** For viewing online documentation

### 4.5 Known Issues and Solutions

1. **Compiler Compatibility:** GFORTRAN compiler is recommended
2. **SQLite Dependencies:** Ensure sqlite3-dev package is installed
3. **Path Issues:** Avoid using excessively long path names
4. **Permission Issues:** Ensure sufficient permissions to access installation directory

### 4.6 Preparation for AiiDA Configuration

Local QUANTICS installation is mainly used for:
- Testing input file formats
- Verifying calculation parameters
- Local small-scale testing
- Understanding software workflows

**Actual production calculations will still be performed on the hartree cluster, where QUANTICS is pre-installed.**

---

## Part 5: Hartree Cluster Configuration

### 5.1 Set Up SSH Keys (If Not Already Done)

```bash
# Generate SSH key pair
ssh-keygen -t rsa -b 4096

# Copy public key to hartree cluster
ssh-copy-id your_username@hartree.chem.ucl.ac.uk

# Test connection
ssh your_username@hartree.chem.ucl.ac.uk
```

### 5.2 Configure AiiDA Computer

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

### 5.3 Verify Computer Configuration

After configuring the computer, run the following verification commands:

```bash
# Test computer connection
verdi computer test hartree

# Show detailed computer information
verdi computer show hartree

# List all configured computers
verdi computer list
```

The expected output of `verdi computer list` should show:
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

**Additional Connection Testing:**
Test direct SSH connection to ensure network connectivity:
```bash
# Test SSH connection and file access (replace ucapjd1 with your username)
ssh ucapjd1@hartree.chem.ucl.ac.uk ls -l ~/aiida_run/test_upload.txt
```

This command verifies:
- SSH connection works properly
- Your credentials are correct
- You can access the hartree filesystem

### 5.4 Configure QUANTICS Code

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

## Part 6: Install GUI Interface Dependencies

### 6.1 Install PyQt5 and Other GUI Dependencies

```bash
# Ensure you're in the aiida virtual environment
source aiida_env/bin/activate

# Install PyQt5
pip install PyQt5

# If in WSL2, install X11 support
sudo apt install python3-pyqt5 python3-pyqt5.qtwidgets
```

### 6.2 Graphics Interface Configuration

#### Native Linux Systems:
Most Linux distributions have built-in X11 support and require no additional configuration.

#### WSL1 (Windows Subsystem for Linux Version 1):

**Step 1: Install X Server on Windows**

1. Download and install VcXsrv (free, open-source):
   - Official download: https://sourceforge.net/projects/vcxsrv/

2. Start VcXsrv with the following settings:
   - Select "Multiple windows"
   - Select "Start no client"
   - In "Extra settings", check "Disable access control" (so WSL1 can connect directly)
   - Click "Finish"
   - VcXsrv icon will appear in the system tray, indicating the service is listening on 0.0.0.0:6000

**Step 2: Set DISPLAY Environment Variable in WSL1**

Open WSL1 terminal and edit `~/.bashrc`:
```bash
# Specify X server address (localhost for WSL1)
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

If you see two small eyes following your mouse on the Windows desktop, X11 forwarding is working.

**WSL1 Troubleshooting:**

If `xeyes` shows "Error: Can't open display:", manually set environment variables in the current session:
```bash
export DISPLAY=localhost:0.0
export LIBGL_ALWAYS_INDIRECT=1
xeyes
```

**Windows Firewall Configuration:**
- Open "Windows Security" → "Firewall & network protection" → "Advanced settings" → "Inbound Rules"
- Create or find a rule: Allow TCP port 6000 inbound connections, targeting "Any" or "vEthernet (WSL)" network

#### WSL2 (Windows Subsystem for Linux Version 2):

```bash
# Install X11 server support
sudo apt install x11-apps

# Set DISPLAY variable in WSL2
echo 'export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk "{print \$2}"):0.0' >> ~/.bashrc
source ~/.bashrc
```

**WSL2 Users Note:** An X11 server (like VcXsrv or X410) needs to be installed on Windows

#### Alternative for Windows 11: WSLg
If you're using Windows 11 with the latest WSL version that includes WSLg:
```powershell
# Update WSL to enable WSLg
wsl --update
```
With WSLg, GUI applications can run directly without needing to install an additional X server.

---

## Part 7: Obtain and Configure QUANTICS GUI

### 7.1 Obtain GUI Files

Ensure you have the following files in your working directory:
- `quantics_gui_pyqt.py` - Local GUI
- `quantics_gui_aiida.py` - AiiDA integrated GUI
- `quantics_aiida_integration.py` - AiiDA integration module

### 7.2 Test AiiDA Configuration

```bash
# Run test in GUI directory
python3 -c "
from quantics_aiida_integration import QuanticsAiidaIntegration
integration = QuanticsAiidaIntegration()
print('AiiDA configuration test:', integration.test_aiida_setup())
"
```

---

## Part 8: Using the GUI Interface

### 8.1 Local Mode GUI

If you only want to run QUANTICS locally (without using the cluster):

```bash
# Activate virtual environment
source aiida_env/bin/activate

# Start local GUI
python3 quantics_gui_pyqt.py
```

### 8.2 AiiDA Integrated GUI (Recommended)

To run calculations using the hartree cluster:

```bash
# Activate virtual environment
source aiida_env/bin/activate

# Ensure AiiDA daemon is running
verdi daemon status

# Start AiiDA GUI
python3 quantics_gui_aiida.py
```

---

## Part 9: GUI Interface Usage Instructions

### 9.1 AiiDA GUI Interface Features

#### Main Components:
1. **Task List Area** - Shows all AiiDA tasks
2. **File Management Area** - Upload and manage input files
3. **Parameter Configuration Area** - Set QUANTICS run parameters
4. **Output Display Area** - View calculation results and logs

#### Basic Usage Workflow:

**Step 1: Prepare Input Files**
1. Click "Browse File" button to select QUANTICS input file (usually `.inp` file)
2. Selected file path will be displayed in the file selection box

**Step 2: Configure Run Parameters**
1. **Job Label:** Give your calculation task a meaningful name
2. **Description:** Optional, describe the purpose of this calculation
3. **Max Wallclock Time:** Set maximum calculation runtime (seconds)
4. **Expected Output Files:** Specify output files to retrieve

**Step 3: Configure Analysis Tools (Optional)**
If you need post-processing analysis of results:
1. Check required analysis tools:
   - `rdcheck natpop` - Check natural transition density
   - `rdcheck flux` - Check flux
   - `rdcheck gdens` - Check density
   - `rdgpop` - Generate transition plots
2. For `rdgpop` tool, you can set:
   - **nz value:** Number of grid points (default: 2)
   - **dof value:** Degree of freedom number (default: 1)
   - **Show command line:** Whether to show detailed commands

**Step 4: Submit Task**
1. Check all parameter settings
2. Click "Submit Job" button
3. Task will be submitted to the hartree cluster

**Step 5: Monitor Task Status**
1. Task list will show all submitted tasks
2. Status includes:
   - `CREATED` - Created
   - `SUBMITTED` - Submitted
   - `RUNNING` - Running
   - `FINISHED` - Completed
   - `FAILED` - Failed
3. Double-click task to view detailed information

**Step 6: View Results**
1. After task completion, click "Show Results" to view output
2. Download output files
3. View analysis tool results (if analysis tools were used)

### 9.2 Common Operations

#### Refresh Task List
```
Click "Refresh" button to update task status
```

#### Clear Task History
```
Select tasks to delete, right-click to select delete
```

#### View Task Details
```
Double-click task row to view detailed information and logs
```

---

## Part 10: Troubleshooting

### 10.1 Common Issues

**Issue 1: PostgreSQL Cannot Start (WSL Environment)**
```bash
# Error message: System has not been booted with systemd as init system
# Solution: Use the following commands instead of systemctl

# Start PostgreSQL service
sudo service postgresql start

# Verify startup success
sudo service postgresql status

# Or check processes
ps aux | grep postgres

# If still cannot connect, try re-initializing database
sudo -u postgres /usr/lib/postgresql/*/bin/initdb -D /var/lib/postgresql/data
```

**Issue 2: RabbitMQ Cannot Start (WSL Environment)**
```bash
# Error message: System has not been booted with systemd as init system
# Solution: Use the following commands instead of systemctl

# Method 1: Use service command
sudo service rabbitmq-server start

# Method 2: Start directly
sudo rabbitmq-server -detached

# Verify startup success
sudo rabbitmqctl status
```

**Issue 3: AiiDA Daemon Cannot Start**
```bash
# Solution
verdi daemon stop
verdi daemon start
```

**Issue 4: Cannot Connect to Hartree Cluster**
```bash
# Test SSH connection
ssh your_username@hartree.chem.ucl.ac.uk

# Reconfigure computer
verdi computer configure core.ssh hartree
```

**Issue 5: GUI Cannot Start (WSL2)**
```bash
# Check X11 forwarding
echo $DISPLAY
xeyes  # Test graphics interface

# Reset DISPLAY variable
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0
```

**Issue 6: QUANTICS Compilation Failed**
```bash
# Check if dependencies are complete
sudo apt install gfortran gcc g++ make sqlite3 libsqlite3-dev

# Check compiler version
gfortran --version

# Clean and recompile
cd ~/quantics/install
make clean
./install_quantics

# Check environment variables
echo $QUANTICS_DIR
menv
```

**Issue 7: Task Submission Failed**
```bash
# Check AiiDA status
verdi status

# View daemon logs
verdi daemon logshow
```

### 10.2 Log File Locations

- **AiiDA Logs:** `~/.aiida/daemon/log/`
- **Task Logs:** View through GUI "Show Results"
- **System Logs:** `/var/log/`

---

## Part 11: Advanced Configuration

### 11.1 Performance Optimization

```bash
# Increase daemon worker processes
verdi daemon incr 4

# Set larger work directory
verdi computer configure core.ssh hartree
# Modify Work directory to larger storage space
```

### 11.2 Custom Analysis Tools

You can add new analysis tools in `quantics_gui_aiida.py`:

```python
# Add new tool in analysis_tools dictionary
'new_tool': {
    'command': 'your_command',
    'description': 'Tool description',
    'requires_params': False  # Whether additional parameters are required
}
```

---

## Part 12: Maintenance and Backup

### 12.1 Database Backup

```bash
# Export AiiDA database
verdi archive create backup.aiida

# Restore database
verdi archive import backup.aiida
```

### 12.2 Regular Maintenance

```bash
# Clean old task data
verdi calcjob cleanworkdir --older-than 30  # Clean work directories older than 30 days

# Check system status
verdi status
verdi daemon status
```

---

## Quick Start Checklist

Before use, ensure the following items are completed:

- [ ] RabbitMQ service running properly (recommended)
- [ ] PostgreSQL database running properly
- [ ] AiiDA profile configured successfully (`verdi status` shows green)
- [ ] AiiDA daemon running (`verdi daemon status` shows running)
- [ ] QUANTICS official documentation read (optional but recommended)
- [ ] Local QUANTICS installation complete (if local testing needed)
- [ ] Hartree cluster SSH connection normal (`verdi computer test hartree` succeeds)
- [ ] QUANTICS code path configured correctly
- [ ] Virtual environment activated
- [ ] GUI dependencies installed
- [ ] X11 forwarding configured correctly (WSL2 users)
- [ ] Storage plugin configured correctly (core.psql_dos recommended)

---

## Technical Support

If you encounter problems, please check:
1. System logs and error messages
2. AiiDA official documentation: https://aiida.readthedocs.io/
3. QUANTICS User Manual
4. Contact system administrator or development team

---

**Last Updated:** December 2024
**Version:** 2.0 (Updated for AiiDA 2.7.0+)
**Authors:** QUANTICS-AiiDA Development Team

## Version Update Notes

### v2.0 (December 2024)
- Updated for AiiDA 2.7.0+ compatibility
- Added RabbitMQ installation instructions
- Updated profile setup commands (using core.psql_dos plugin)
- Added verdi presto automated configuration option
- Improved PostgreSQL database configuration process
- Enhanced storage plugin selection guide
- Added complete QUANTICS software installation guide
- Added QUANTICS system requirements and dependency descriptions
- Included local installation and parallel compilation options
