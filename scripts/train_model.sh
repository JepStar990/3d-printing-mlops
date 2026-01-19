#!/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "Training ML model for surface roughness prediction..."

# Activate virtual environment if present (optional)
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Set PYTHONPATH to include the project root for utils imports
export PYTHONPATH="$PWD:$PYTHONPATH"

cd real-time-engine

# Run training script
python train_model.py

echo "Training finished. Model saved to models/model.pkl"
