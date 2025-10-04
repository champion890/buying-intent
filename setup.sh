#!/bin/bash

set -e  # Exit on error
echo "Starting setup..."

# Remove existing venv if exists
if [ -d "venv" ]; then
    echo "Removing existing venv..."
    rm -rf venv
fi

# Ensure python3 and pip are installed
echo "Checking Python installation..."
which python3 || (echo "Python3 not found!" && exit 1)
python3 --version

# Create new venv without pip
echo "Creating virtual environment..."
python3 -m venv venv --without-pip

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Install pip manually using the correct URL for Python 3.8
echo "Installing pip..."
curl https://bootstrap.pypa.io/pip/3.8/get-pip.py -o get-pip.py
python3 get-pip.py
rm get-pip.py

# Verify pip installation
echo "Verifying pip installation..."
which pip
pip --version

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

echo "Setup completed successfully!"
