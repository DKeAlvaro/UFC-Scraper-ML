# UFC Model Update Script for Windows Task Scheduler
# This script safely updates models with resource limits and pushes logs to git

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

# Function to safely execute git commands
function Invoke-GitCommand {
    param($Command, $Description)
    try {
        Write-Log "Git: $Description"
        $result = Invoke-Expression "git $Command" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Git: $Description completed successfully"
            if ($result) { Write-Log "Git output: $result" }
            return $true
        } else {
            Write-Log "Git: $Description failed with exit code $LASTEXITCODE"
            Write-Log "Git error: $result"
            return $false
        }
    } catch {
        Write-Log "Git: Error executing $Description - $($_.Exception.Message)"
        return $false
    }
}

# Function to commit and push changes
function Push-ChangesToGit {
    Write-Log "Starting git operations..."
    
    # Check if we're in a git repository
    if (!(Test-Path ".git")) {
        Write-Log "Not in a git repository. Skipping git operations."
        return
    }
    
    # Check git status
    $gitStatus = git status --porcelain 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Failed to check git status. Skipping git operations."
        return
    }
    
    if ([string]::IsNullOrWhiteSpace($gitStatus)) {
        Write-Log "No changes to commit."
        return
    }
    
    # Add all changes
    if (!(Invoke-GitCommand "add ." "Adding all changes")) {
        return
    }
    
    # Create commit message with timestamp
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $commitMessage = "Automated model update: $timestamp"
    
    # Commit changes
    if (!(Invoke-GitCommand "commit -m `"$commitMessage`"" "Committing changes")) {
        return
    }
    
    # Push to remote
    if (!(Invoke-GitCommand "push" "Pushing to remote repository")) {
        Write-Log "Failed to push changes. Changes are committed locally."
        return
    }
    
    Write-Log "Successfully pushed all changes to git repository."
}

# Check if another update is already running
if (Test-Path $LOCK_FILE) {
    Write-Log "Another update process is already running. Exiting."
    exit 1
}

# Create lock file
$PID | Out-File -FilePath $LOCK_FILE

try {
    Write-Log "Starting automated model update and git sync..."
    
    # Change to project directory
    Set-Location $PROJECT_DIR
    
    # Verify we're in the right directory
    if (!(Test-Path "src\main.py")) {
        Write-Log "Error: Not in UFC project directory. Expected to find src\main.py"
        exit 1
    }
    
    # Create a job to run the update with timeout
    Write-Log "Running model update pipeline..."
    $job = Start-Job -ScriptBlock {
        param($projectDir)
        Set-Location $projectDir
        python -m src.main --pipeline update 2>&1
    } -ArgumentList $PROJECT_DIR
    
    # Wait for job completion with timeout
    $updateSuccess = $false
    if (Wait-Job $job -Timeout ($MAX_TIMEOUT_MINUTES * 60)) {
        $result = Receive-Job $job
        $exitCode = $job.State
        
        if ($exitCode -eq "Completed") {
            Write-Log "Model update pipeline completed successfully."
            Write-Log "Pipeline output: $result"
            $updateSuccess = $true
        } else {
            Write-Log "Model update pipeline failed. State: $exitCode"
            Write-Log "Pipeline output: $result"
        }
    } else {
        Write-Log "Model update timed out after $MAX_TIMEOUT_MINUTES minutes. Stopping job."
        Stop-Job $job
    }
    
    Remove-Job $job -Force
    
    # Always attempt to push logs and any changes to git
    Write-Log "Syncing changes to git repository..."
    Push-ChangesToGit
    
    if ($updateSuccess) {
        Write-Log "Automated update completed successfully with git sync."
    } else {
        Write-Log "Automated update completed with errors, but logs have been synced to git."
    }
    
} catch {
    Write-Log "Critical error during automated update: $($_.Exception.Message)"
    
    # Try to push error logs to git
    try {
        Set-Location $PROJECT_DIR
        Push-ChangesToGit
    } catch {
        Write-Log "Failed to push error logs to git: $($_.Exception.Message)"
    }
} finally {
    # Cleanup lock file
    if (Test-Path $LOCK_FILE) {
        Remove-Item $LOCK_FILE -Force
    }
    Write-Log "Automated update process finished."
} 