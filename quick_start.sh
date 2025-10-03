#!/bin/bash

# Quick Start Script for Multiprocessing Server Demo
# This script sets up and runs a complete demonstration

echo "=========================================="
echo "Multiprocessing Server Quick Start"
echo "=========================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed or not in PATH"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Make scripts executable
chmod +x server.py
chmod +x client_simulator.py
chmod +x performance_monitor.py
chmod +x test_runner.py
chmod +x run_demo.py

echo "=========================================="
echo "Setup complete! Choose an option:"
echo "=========================================="
echo "1. Run basic demo (single client, 1kHz)"
echo "2. Run multiprocess demo (4 clients, 2kHz each)"
echo "3. Run stress test (8 clients, 1kHz each)"
echo "4. Run automated test suite"
echo "5. Start server only"
echo "6. Start client simulator only"
echo "=========================================="

read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        echo "Running basic demo..."
        python3 run_demo.py --scenario basic
        ;;
    2)
        echo "Running multiprocess demo..."
        python3 run_demo.py --scenario multiprocess
        ;;
    3)
        echo "Running stress test..."
        python3 run_demo.py --scenario stress
        ;;
    4)
        echo "Running automated test suite..."
        python3 test_runner.py
        ;;
    5)
        echo "Starting server..."
        python3 server.py
        ;;
    6)
        echo "Starting client simulator..."
        python3 client_simulator.py
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo "=========================================="
echo "Done!"
echo "=========================================="
