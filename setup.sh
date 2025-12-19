#!/bin/bash

# An0m0s VPN Manager - Quick Setup Script
# This script helps you quickly set up the application

set -e

echo "================================================"
echo "   An0m0s VPN Manager - Setup Script"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "⚠️  Please do NOT run this setup script as root!"
    echo "   Run it as your normal user. The app will request"
    echo "   elevated privileges when needed."
    exit 1
fi

# Check Python version
echo "📋 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "   Install it with: sudo apt install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION found"

# Check system dependencies
echo ""
echo "📋 Checking system dependencies..."

MISSING_DEPS=()

if ! command -v openvpn &> /dev/null; then
    MISSING_DEPS+=("openvpn")
fi

if ! command -v iptables &> /dev/null; then
    MISSING_DEPS+=("iptables")
fi

if ! python3 -c "import tkinter" 2>/dev/null; then
    MISSING_DEPS+=("python3-tk")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "❌ Missing dependencies: ${MISSING_DEPS[*]}"
    echo ""
    echo "Install them with:"
    echo "   sudo apt update"
    echo "   sudo apt install ${MISSING_DEPS[*]}"
    echo ""
    read -p "Would you like to install them now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt update
        sudo apt install ${MISSING_DEPS[*]}
    else
        exit 1
    fi
else
    echo "✅ All system dependencies installed"
fi

# Create virtual environment
echo ""
echo "📦 Setting up Python virtual environment..."
if [ -d "env" ]; then
    echo "⚠️  Virtual environment already exists"
    read -p "Recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf env
        python3 -m venv env
    fi
else
    python3 -m venv env
fi

# Activate and install dependencies
echo ""
echo "📥 Installing Python dependencies..."
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "================================================"
echo "   How to run An0m0s VPN Manager:"
echo "================================================"
echo ""
echo "Option 1 (Recommended):"
echo "   pkexec python3 An0m0s_vpn.py"
echo ""
echo "Option 2:"
echo "   sudo python3 An0m0s_vpn.py"
echo ""
echo "================================================"
echo ""

# Make the main script executable
chmod +x An0m0s_vpn.py

echo "🚀 Ready to launch!"
echo ""
