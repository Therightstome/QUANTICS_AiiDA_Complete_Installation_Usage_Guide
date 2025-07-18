# QUANTICS AiiDA Complete Installation & Usage Guide

This repository contains scripts to integrate the QUANTICS quantum dynamics package with AiiDA for automated workflows. Below is an overview of the files and how to get started.

## Repository Contents

* **quantics\_gui\_aiida.py**
  A simple graphical user interface to launch QUANTICS calculations through AiiDA.

* **quantics\_local\_runner.py**
  Script to run QUANTICS workflows locally without a scheduler, using AiiDA's `run` function.

* **quantics\_aiida\_integration.py**
  Core integration script demonstrating how to set up AiiDA `CalcJobs` for QUANTICS, define input files, and parse outputs.

* **README.md**
  This usage guide.

## Getting Started

1. **Clone this repository** into a local folder:

   ```bash
   git clone https://github.com/Therightstome/QUANTICS_AiiDA_Complete_Installation_Usage_Guide.git
   cd QUANTICS_AiiDA_Complete_Installation_Usage_Guide
   ```

2. **Ensure your environment** has:

   * A working QUANTICS installation
   * A configured AiiDA profile (e.g., `verdi status` ✅)
   * Python dependencies installed (e.g., `pip install aiida-core`).

3. **Download all files** in this repo into a single folder (no further hierarchy needed).

4. **Launch the GUI interface** to run a QUANTICS calculation via AiiDA:

   ```bash
   python quantics_gui_aiida.py
   ```

   Follow on-screen prompts to select input files and submit workflows.

5. **Use the local runner** for testing without daemon:

   ```bash
   python quantics_local_runner.py
   ```

6. **Inspect the core integration script** (`quantics_aiida_integration.py`) to learn how to:

   * Define inputs
   * Connect QUANTICS code to AiiDA
   * Retrieve and parse outputs

## Customization

Feel free to adapt the scripts to your own QUANTICS input formats, AiiDA profiles, or computational resources. Comments are provided inline for easy customization.

---

Happy calculations with QUANTICS & AiiDA!
