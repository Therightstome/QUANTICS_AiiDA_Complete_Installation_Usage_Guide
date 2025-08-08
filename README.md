# QUANTICS Professional GUI

A professional interface for QUANTICS quantum dynamics calculations with support for both local execution and AiiDA workflow management.

## Requirements

- Python 3.8+
- PyQt5 or PySide2 (GUI framework)
- QUANTICS software (quantum dynamics calculations)
- AiiDA (optional, for cluster calculations)

Install the required packages:

```bash
pip install -r requirements.txt
```

For AiiDA support:
```bash
pip install -r requirements.txt
pip install aiida-core
```

## Usage

### GUI Mode (Recommended)

Start the graphical interface:

```bash
python quantics_gui.py
```

### Command Line Interface

Create and run a calculation:

```bash
# Create calculation
python quantics_gui.py create my_calc examples/example_inputs/ho.inp examples/example_inputs/ho.op --workflow MCTDH

# Run calculation  
python quantics_gui.py run my_calc

# Run analysis
python quantics_gui.py analyze my_calc "rdcheck etot" "rdcheck spop"

# Check status
python quantics_gui.py status

# Run built-in example
python quantics_gui.py example
```

### First Calculation

For a quick test:

1. Start the GUI: `python quantics_gui.py`
2. Select "Local Execution" mode
3. Choose workflow type: "MCTDH"
4. Browse to input files: `examples/example_inputs/ho.inp` and `ho.op`
5. Select analysis tools: "rdcheck etot" and "rdcheck spop"
6. Click "Start Calculation"

## Project Structure

```
quantics_professional_gui/
├── quantics_gui.py              # Main entry point
├── requirements.txt             # Dependencies
├── setup.py                    # Package installation
├── README.md                   # This file
├── INSTALL.md                  # Installation guide
├── quantics_env.sh             # Environment setup
│
├── src/                        # Source modules
│   ├── gui/                    # GUI components
│   ├── runners/                # Calculation engines
│   └── utils/                  # Utilities
│
├── examples/                   # Examples and documentation
│   ├── example_inputs/         # Sample input files
│   └── quick_start_guide.md   # Quick start tutorial
│
└── docs/                      # Full documentation
    ├── QUANTICS_AiiDA_Complete_Installation_Usage_Guide.md
    └── QUANTICS_AiiDA_完整安装使用指南.md
```

## Features

- **Dual execution modes**: Local computation and AiiDA cluster workflows
- **Multiple workflow types**: MCTDH, vMCG, DD-vMCG support
- **Integrated analysis tools**: Automated post-processing with rdcheck, rdgpop, ddtraj
- **Configuration management**: Save/load calculation settings
- **Cross-platform**: Linux, macOS, Windows (with WSL2)
- **Example files**: Ready-to-use harmonic oscillator and double well examples

## Analysis Tools

| Tool | Description | Workflows |
|------|-------------|-----------|
| `rdcheck etot` | Energy conservation analysis | All |
| `rdcheck spop` | Single particle populations | All |
| `rdcheck natpop` | Natural population analysis | MCTDH |
| `rdgpop` | Grid population analysis | MCTDH, vMCG |
| `ddtraj` | Direct dynamics trajectories | DD-vMCG |

## Testing and Formatting (Work in Progress)

Testing is done through the pytest framework:

```bash
pip install pytest
pytest tests/
```

Formatting is done using black:

```bash
pip install black
black .
```

## Installation

For detailed installation instructions including AiiDA setup, see [INSTALL.md](INSTALL.md).

For a complete guide with cluster configuration, see [docs/QUANTICS_AiiDA_Complete_Installation_Usage_Guide.md](docs/QUANTICS_AiiDA_Complete_Installation_Usage_Guide.md).

## Examples

The `examples/` directory contains:
- **Harmonic oscillator** (`ho.inp`, `ho.op`): Simple test case
- **Double well potential** (`double_well.inp`, `double_well.op`): More complex dynamics

An example Jupyter notebook is provided to demonstrate usage:

```bash
jupyter notebook examples/quantics_gui_demo.ipynb
```

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- QUANTICS development team for the core quantum dynamics software
- AiiDA team for the workflow management framework
- PyQt/PySide developers for the GUI framework
