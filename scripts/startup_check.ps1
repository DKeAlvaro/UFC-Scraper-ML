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

try {
    Write-Log "Startup model check initiated..."
    Set-Location $PROJECT_DIR
    
    # Run a quick check (won't retrain unless needed)
    $result = python -m src.main --pipeline update 2>&1
    Write-Log "Update result: $result"
    
    if ($result -like "*retraining*") {
        # Show notification if models were updated
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show("UFC models were updated with new data!", "Model Update", "OK", "Information")
    }
    
} catch {
    Write-Log "Error during startup check: $($_.Exception.Message)"
}

Write-Log "Startup check completed." 