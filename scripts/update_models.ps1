# UFC Model Update Script for Windows Task Scheduler
# This script safely updates models with resource limits

# Configuration
$PROJECT_DIR = "C:\Users\Alvaro\Desktop\ufc"  # Change this to your actual path
$LOG_DIR = "$PROJECT_DIR\logs"
$LOG_FILE = "$LOG_DIR\model_update.log"
$LOCK_FILE = "$LOG_DIR\update.lock"
$MAX_TIMEOUT_MINUTES = 120  # 2 hours timeout

# Create logs directory if it doesn't exist
if (!(Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force
}

# Function to log with timestamp
function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$timestamp] $Message" | Out-File -FilePath $LOG_FILE -Append
    Write-Host "[$timestamp] $Message"
}

# Check if another update is already running
if (Test-Path $LOCK_FILE) {
    Write-Log "Another update process is already running. Exiting."
    exit 1
}

# Create lock file
$PID | Out-File -FilePath $LOCK_FILE

try {
    Write-Log "Starting model update check..."
    
    # Change to project directory
    Set-Location $PROJECT_DIR
    
    # Create a job to run the update with timeout
    $job = Start-Job -ScriptBlock {
        param($projectDir)
        Set-Location $projectDir
        python -m src.main --pipeline update
    } -ArgumentList $PROJECT_DIR
    
    # Wait for job completion with timeout
    if (Wait-Job $job -Timeout ($MAX_TIMEOUT_MINUTES * 60)) {
        $result = Receive-Job $job
        $exitCode = $job.State
        
        if ($exitCode -eq "Completed") {
            Write-Log "Model update completed successfully."
            Write-Log "Output: $result"
        } else {
            Write-Log "Model update failed. State: $exitCode"
        }
    } else {
        Write-Log "Model update timed out after $MAX_TIMEOUT_MINUTES minutes. Stopping job."
        Stop-Job $job
    }
    
    Remove-Job $job -Force
    
} catch {
    Write-Log "Error during model update: $($_.Exception.Message)"
} finally {
    # Cleanup lock file
    if (Test-Path $LOCK_FILE) {
        Remove-Item $LOCK_FILE -Force
    }
    Write-Log "Update check completed."
} 