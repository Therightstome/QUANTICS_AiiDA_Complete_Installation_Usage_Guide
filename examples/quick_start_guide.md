# QUANTICS Professional GUI - Quick Start Guide

## Overview

This guide will help you get started with the QUANTICS Professional GUI in just a few minutes.

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up QUANTICS environment:**
   ```bash
   # Make sure quantics command is available
   which quantics
   
   # If not available, set up your QUANTICS environment
   export QUANTICS_HOME=/path/to/quantics
   export PATH=$QUANTICS_HOME/bin/binary/x86_64:$PATH
   ```

## Quick Start

### 1. Start the GUI

Simply run:
```bash
python quantics_gui.py
```

### 2. Run Your First Calculation

1. **Choose execution mode:** Select "Local Execution" for testing
2. **Set calculation name:** Enter "my_first_run"  
3. **Select workflow type:** Choose "MCTDH"
4. **Select input files:**
   - `.inp file`: Browse to `examples/example_inputs/ho.inp`
   - `.op file`: Browse to `examples/example_inputs/ho.op`
5. **Choose analysis tools:** Select "rdcheck etot" and "rdcheck spop"
6. **Start calculation:** Click "Start Calculation"

### 3. View Results

After the calculation completes:
- Check the log panel for progress information
- View output files in the Results Browser
- Analysis results will be automatically generated

## Example Files

### Harmonic Oscillator (ho.inp/ho.op)
- Simple 1D harmonic oscillator
- Good for testing basic QUANTICS functionality
- Quick calculation (~30 seconds)

### Double Well (double_well.inp/double_well.op)  
- 1D double well potential with tunneling dynamics
- More complex physics demonstration
- Longer calculation time (~5 minutes)

## Command Line Interface

You can also use the command line interface:

```bash
# Create a calculation
python quantics_gui.py create test_calc examples/example_inputs/ho.inp examples/example_inputs/ho.op

# Run the calculation
python quantics_gui.py run test_calc

# Run analysis
python quantics_gui.py analyze test_calc "rdcheck etot" "rdcheck spop"

# Check status
python quantics_gui.py status

# Run built-in example
python quantics_gui.py example
```

## GUI Features

### Execution Modes
- **Local Execution**: Run calculations on your local machine
- **AiiDA Workflow**: Submit calculations to HPC clusters (requires AiiDA setup)

### Analysis Tools
- `rdcheck etot`: Check energy conservation
- `rdcheck spop`: Analyze single particle populations  
- `rdcheck natpop`: Natural population analysis
- `rdgpop`: Grid population analysis with visualization
- `ddtraj`: Direct dynamics trajectory analysis (DD-vMCG only)

### Configuration Management
- Save/Load calculation configurations
- Reuse settings for similar calculations
- Export configurations for sharing

## Tips

1. **Start with local execution** to test your input files
2. **Use small examples** first to verify QUANTICS is working
3. **Check the log panel** for detailed calculation progress
4. **Save configurations** for calculations you want to repeat
5. **Use analysis tools** to understand your calculation results

## Troubleshooting

### GUI won't start
```bash
# Check dependencies
pip install PyQt5

# Check Python path
python -c "import sys; print(sys.path)"
```

### Calculation fails
1. Check that QUANTICS is properly installed
2. Verify input file syntax
3. Check the calculation log for error messages
4. Try the built-in example first: `python quantics_gui.py example`

### Need help?
- Check the full installation guide: `QUANTICS_AiiDA_Complete_Installation_Usage_Guide.md`
- Review the calculation logs for specific error messages
- Test with the provided example files first

## Next Steps

Once you're comfortable with the basic usage:

1. **Set up AiiDA** for cluster calculations (see full installation guide)
2. **Create your own input files** for your specific research
3. **Explore advanced analysis tools** and parameters
4. **Use the command line interface** for automated workflows

Happy calculating! 