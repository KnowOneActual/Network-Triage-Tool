#!/bin/bash
# This script reliably launches the Network Triage Tool.

# Get the directory of this script, which is the project root.
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Define the full path to the python executable inside the virtual environment.
PYTHON_EXEC="$DIR/.venv/bin/python3"

# Change the current directory to the project root. This is crucial.
cd "$DIR"

# Run the python module using the specific python from the virtual environment.
# This ensures it can find 'src' and all installed libraries.
"$PYTHON_EXEC" -m src.macos.main_app