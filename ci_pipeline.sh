#!/bin/bash

# Ensure we exit the script on any error
set -e

# Print the Python version (for debugging purposes)
echo "Using Python version:"
python --version

# Step 1: Install dependencies (including development dependencies)
echo "Installing dependencies..."
pdm install --dev

# Step 2: Run linting (Pylint)
echo "Running pylint..."
pdm run pylint semantiva --fail-under=7.5

# Step 3: Run black (code formatting check)
echo "Running black..."
pdm run black --check semantiva

# Step 4: Run tests using pytest
echo "Running pytest..."
pdm run pytest --maxfail=1 --disable-warnings -q

# You can add more steps here as needed (e.g., build, deploy, etc.)
echo "Pipeline finished successfully."