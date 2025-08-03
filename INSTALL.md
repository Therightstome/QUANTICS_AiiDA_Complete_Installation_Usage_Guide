# 🚀 QUANTICS Professional GUI - Installation Guide

## Quick Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start GUI
```bash
python quantics_gui.py
```

That's it! The GUI will launch and you can start using it immediately.

## First Run

1. **Select "Local Execution"** mode for testing
2. **Browse to example files:**
   - `.inp file`: `examples/example_inputs/ho.inp`
   - `.op file`: `examples/example_inputs/ho.op`
3. **Select analysis tools:** `rdcheck etot` and `rdcheck spop`
4. **Click "Start Calculation"**

## Development Installation

For development with optional AiiDA support:

```bash
# Install with AiiDA support
pip install -e .[aiida]

# Install development tools
pip install -e .[dev]

# Format code
black .

# Run tests (when available)
pytest
```

## System Requirements

- **Python:** 3.8+
- **Operating System:** Linux, macOS, Windows (with WSL2)
- **QUANTICS:** Must be installed and available in PATH
- **GUI Framework:** PyQt5 or PySide2

## Quick Test

Test the installation with the built-in example:

```bash
python quantics_gui.py example
```

This will run a harmonic oscillator calculation if QUANTICS is properly installed.

## Need Help?

- **Quick Start:** See `examples/quick_start_guide.md`
- **Full Documentation:** See `docs/QUANTICS_AiiDA_Complete_Installation_Usage_Guide.md`

### GUI won't start
```bash
pip install PyQt5
```

### QUANTICS not found
```bash
# Make sure QUANTICS is in your PATH
which quantics

# Or set up environment
source quantics_env.sh
```

### Import errors
```bash
# Check if you're in the right directory
ls quantics_gui.py

# Check Python path
python -c "import sys; print(sys.path)"
``` 