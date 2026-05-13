#!/bin/bash

# Capture the required variables
host=$(hostname)
SLEEP_TIME=$1 # in seconds
FILE_SIZE=$2 # in MB
DEST_DIR=$3
RANK=$4

# Check if PMIX_RANK is set to prevent directory errors
if [ -z "$RANK" ]; then
    echo "Error: PMIX_RANK environment variable is not set."
    exit 1
fi

# Define paths and parameters
TMP_DIR="/tmp/data"
TEMP_FILE="${TMP_DIR}/${RANK}.dat"
#DEST_DIR="/flare/datascience/csimpson/toy_test/test/${host}/"

# Ensure the destination directory exists (only needs to be created once)
mkdir -p "$TMP_DIR"
mkdir -p "$DEST_DIR"

echo "---------------------------------------------------"
echo "[Host: $host | Rank: $RANK | Iteration: $iteration]"
    
# 1. Write a 100 MB file to /tmp/${RANK}
echo "Creating $FILE_SIZE MB file at $TEMP_FILE..."
dd if=/dev/zero of="$TEMP_FILE" bs=1M count=$FILE_SIZE 2>/dev/null

# 2. Sleep for a time seconds
echo "Sleeping for a time seconds..."
sleep $SLEEP_TIME

# 3. Move the file to the target subdirectory
mv "$TEMP_FILE" "$DEST_DIR/"

echo "File successfully moved to: $DEST_DIR/"
