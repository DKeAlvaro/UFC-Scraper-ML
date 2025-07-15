# UFC Model Update - Run on Startup
# This script runs when you start your laptop and checks for model updates

$PROJECT_DIR = "C:\Users\Alvaro\Desktop\ufc"
$LOG_FILE = "$PROJECT_DIR\logs\startup_update.log"

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
            return $true
        } else {
            Write-Log "Git: $Description failed with exit code $LASTEXITCODE"
            return $false
        }
    } catch {
        Write-Log "Git: Error executing $Description - $($_.Exception.Message)"
        return $false
    }
}

# Function to commit and push changes
function Push-ChangesToGit {
    if (!(Test-Path ".git")) {
        Write-Log "Not in a git repository. Skipping git operations."
        return
    }
    
    # Check git status
    $gitStatus = git status --porcelain 2>&1
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($gitStatus)) {
        Write-Log "No changes to commit or git error."
        return
    }
    
    # Add and commit changes
    if ((Invoke-GitCommand "add ." "Adding startup changes") -and 
        (Invoke-GitCommand "commit -m `"Startup model check: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`"" "Committing startup changes")) {
        Invoke-GitCommand "push" "Pushing startup changes to remote"
    }
}

try {
    Write-Log "Startup model check initiated..."
    Set-Location $PROJECT_DIR
    
    # Run a quick check (won't retrain unless needed)
    Write-Log "Running model update pipeline..."
    $result = python -m src.main --pipeline update 2>&1
    Write-Log "Pipeline result: $result"
    
    # Push logs and any changes to git
    Write-Log "Syncing changes to git repository..."
    Push-ChangesToGit
    
    if ($result -like "*retraining*" -or $result -like "*new data*") {
        # Show notification if models were updated
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show("UFC models were updated with new data and synced to git!", "Model Update", "OK", "Information")
        Write-Log "Models were updated and synced to git."
    } else {
        Write-Log "No model updates needed, logs synced to git."
    }
    
} catch {
    Write-Log "Error during startup check: $($_.Exception.Message)"
    
    # Try to push error logs to git
    try {
        Push-ChangesToGit
    } catch {
        Write-Log "Failed to push error logs to git: $($_.Exception.Message)"
    }
}

Write-Log "Startup check completed." 