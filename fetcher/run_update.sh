#!/bin/bash

# Change to the script's directory to ensure relative paths work correctly
cd /root/poly-data

# This script runs the Python update script and logs its output.
# It uses a lock file to prevent multiple instances from running at the same time.

LOG_FILE="/root/poly-data/update_all.log"
LOCK_FILE="/root/poly-data/update_all.lock"

# Check if the lock file exists
if [ -e "$LOCK_FILE" ]; then
    echo "Update script is already running."
    exit 1
fi

# Create the lock file
touch "$LOCK_FILE"

# Activate the virtual environment
source /root/poly-data/.venv/bin/activate

# Run the Python script and log the output
echo "Starting update at $(date)" >> "$LOG_FILE"
python /root/poly-data/fetcher/update_all.py >> "$LOG_FILE" 2>&1
echo "Finished update at $(date)" >> "$LOG_FILE"

# Remove the lock file
rm "$LOCK_FILE"
