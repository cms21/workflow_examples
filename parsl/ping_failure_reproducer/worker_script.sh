#!/bin/bash

# Capture the required variables
host=$(hostname)
RANK="${PMIX_RANK}"

# Check if PMIX_RANK is set to prevent directory errors
if [ -z "$RANK" ]; then
    echo "Error: PMIX_RANK environment variable is not set."
    exit 1
fi

# Define paths and parameters
TMP_DIR="/tmp/data"
TEMP_FILE="${TMP_DIR}/${RANK}.dat"
#DEST_DIR="/flare/datascience/csimpson/toy_test/test/${host}/"

TASK_SCRIPT=$*

# Ensure the destination directory exists (only needs to be created once)
mkdir -p "$TMP_DIR"
mkdir -p "$DEST_DIR"

iteration=1

# Continuous loop
while true; do
    $TASK_SCRIPT $RANK
    # Increment the iteration counter
    ((iteration++))
done
