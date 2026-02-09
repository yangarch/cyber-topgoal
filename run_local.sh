#!/bin/bash

# Define directories
MUSIC_DIR="./music_files"
DATA_DIR="./data"

# Create directories if they don't exist
mkdir -p "$MUSIC_DIR" "$DATA_DIR"

# Set environment variables
export MUSIC_DIR="$MUSIC_DIR"
export DATA_DIR="$DATA_DIR"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run server
echo "Starting server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
