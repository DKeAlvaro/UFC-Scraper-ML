#!/bin/bash

# UFC Model Update Script for Cron
# This script safely updates models with resource limits

# Configuration
PROJECT_DIR="/path/to/your/ufc"  # Change this to your actual path
LOG_FILE="$PROJECT_DIR/logs/model_update.log"
LOCK_FILE="$PROJECT_DIR/logs/update.lock"
MAX_MEMORY="4G"  # Limit memory usage
NICE_LEVEL="10"  # Lower priority (higher number = lower priority)

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check if another update is already running
if [ -f "$LOCK_FILE" ]; then
    log "Another update process is already running. Exiting."
    exit 1
fi

# Create lock file
echo $$ > "$LOCK_FILE"

# Cleanup function
cleanup() {
    rm -f "$LOCK_FILE"
    log "Update process finished."
}

# Set trap to cleanup on exit
trap cleanup EXIT

log "Starting model update check..."

# Change to project directory
cd "$PROJECT_DIR"

# Run the update with resource limits
# nice: lower CPU priority
# timeout: kill if it takes longer than 2 hours
# ulimit: limit memory usage
nice -n "$NICE_LEVEL" timeout 7200 bash -c "
    ulimit -v $((4 * 1024 * 1024))  # 4GB virtual memory limit
    python -m src.main --pipeline update 2>&1
" >> "$LOG_FILE" 2>&1

# Check exit code
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    log "Model update completed successfully."
elif [ $EXIT_CODE -eq 124 ]; then
    log "Model update timed out after 2 hours."
elif [ $EXIT_CODE -eq 137 ]; then
    log "Model update killed due to memory limit."
else
    log "Model update failed with exit code: $EXIT_CODE"
fi

log "Update check completed." 