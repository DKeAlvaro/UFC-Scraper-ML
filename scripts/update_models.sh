#!/bin/bash

# UFC Model Update Script for Cron
# This script safely updates models with resource limits and pushes logs to git

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
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to safely execute git commands
git_command() {
    local command="$1"
    local description="$2"
    
    log "Git: $description"
    if output=$(git $command 2>&1); then
        log "Git: $description completed successfully"
        if [ -n "$output" ]; then
            log "Git output: $output"
        fi
        return 0
    else
        log "Git: $description failed with exit code $?"
        log "Git error: $output"
        return 1
    fi
}

# Function to commit and push changes
push_changes_to_git() {
    log "Starting git operations..."
    
    # Check if we're in a git repository
    if [ ! -d ".git" ]; then
        log "Not in a git repository. Skipping git operations."
        return
    fi
    
    # Check git status
    if ! git_status=$(git status --porcelain 2>&1); then
        log "Failed to check git status. Skipping git operations."
        return
    fi
    
    if [ -z "$git_status" ]; then
        log "No changes to commit."
        return
    fi
    
    # Add all changes
    if ! git_command "add ." "Adding all changes"; then
        return
    fi
    
    # Create commit message with timestamp
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local commit_message="Automated model update: $timestamp"
    
    # Commit changes
    if ! git_command "commit -m \"$commit_message\"" "Committing changes"; then
        return
    fi
    
    # Push to remote
    if ! git_command "push" "Pushing to remote repository"; then
        log "Failed to push changes. Changes are committed locally."
        return
    fi
    
    log "Successfully pushed all changes to git repository."
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
    log "Automated update process finished."
}

# Set trap to cleanup on exit
trap cleanup EXIT

log "Starting automated model update and git sync..."

# Change to project directory
cd "$PROJECT_DIR"

# Verify we're in the right directory
if [ ! -f "src/main.py" ]; then
    log "Error: Not in UFC project directory. Expected to find src/main.py"
    exit 1
fi

log "Running model update pipeline..."

# Run the update with resource limits
# nice: lower CPU priority
# timeout: kill if it takes longer than 2 hours
# ulimit: limit memory usage
UPDATE_SUCCESS=false
nice -n "$NICE_LEVEL" timeout 7200 bash -c "
    ulimit -v $((4 * 1024 * 1024))  # 4GB virtual memory limit
    python -m src.main --pipeline update 2>&1
" >> "$LOG_FILE" 2>&1

# Check exit code
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    log "Model update pipeline completed successfully."
    UPDATE_SUCCESS=true
elif [ $EXIT_CODE -eq 124 ]; then
    log "Model update timed out after 2 hours."
elif [ $EXIT_CODE -eq 137 ]; then
    log "Model update killed due to memory limit."
else
    log "Model update pipeline failed with exit code: $EXIT_CODE"
fi

# Always attempt to push logs and any changes to git
log "Syncing changes to git repository..."
push_changes_to_git

if [ "$UPDATE_SUCCESS" = true ]; then
    log "Automated update completed successfully with git sync."
else
    log "Automated update completed with errors, but logs have been synced to git."
fi 