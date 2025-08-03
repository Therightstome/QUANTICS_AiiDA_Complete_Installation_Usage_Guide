#!/bin/bash
# QUANTICS Environment Setup Script
# Run this script if you need to set up QUANTICS environment manually

echo "Setting up QUANTICS environment..."

export QUANTICS_HOME=/home/jiajun/quantics
export PATH=$QUANTICS_HOME/bin/binary/x86_64:$PATH
export LD_LIBRARY_PATH=$QUANTICS_HOME/bin/dyn_libs:$LD_LIBRARY_PATH

# Activate virtual environment if available
if [ -f /home/jiajun/test/venv/bin/activate ]; then
    source /home/jiajun/test/venv/bin/activate
    echo "Virtual environment activated"
fi

echo "QUANTICS environment ready!"
echo "QUANTICS executable: $(which quantics)"
echo "Analysis tools available: rdcheck, rdgpop, etc."

# Test QUANTICS availability
if command -v quantics &> /dev/null; then
    echo "✅ QUANTICS is available"
else
    echo "❌ QUANTICS not found in PATH"
fi

if command -v rdcheck &> /dev/null; then
    echo "✅ Analysis tools are available"
else
    echo "❌ Analysis tools not found in PATH"
fi 