#!/bin/bash
# Start the Product Review Insights API
cd "$(dirname "$0")/backend"
echo "Starting API on http://localhost:8000 ..."
python3 main.py
