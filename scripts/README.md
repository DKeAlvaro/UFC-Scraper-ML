# UFC Prediction Pipeline Automation Scripts

This directory contains automation scripts that run the UFC prediction pipeline and automatically push logs and model updates to your git repository.

## Scripts Overview

### 1. `update_models.ps1` (Windows PowerShell)
Production-ready automation script for Windows Task Scheduler with git integration.

**Features:**
- Runs model updates with resource limits and timeouts
- Commits and pushes logs to git repository automatically
- Handles missing models and new data detection
- Comprehensive error handling and logging
- Lock file mechanism to prevent concurrent runs

### 2. `update_models.sh` (Linux/Unix Bash)
Production-ready automation script for cron jobs with git integration.

**Features:**
- Same functionality as PowerShell version but for Unix systems
- Memory and CPU resource limits
- Git integration for automatic log syncing
- Process locking and error recovery

### 3. `startup_check.ps1` (Windows Startup)
Lightweight script that runs when you start your laptop.

**Features:**
- Quick model update check on system startup
- Desktop notification if models are updated
- Automatic git sync of startup logs
- Minimal resource usage

## Setup Instructions

### Prerequisites

1. **Git Repository Setup**
   ```bash
   # Make sure your UFC project is a git repository
   cd /path/to/ufc
   git init  # if not already a git repo
   git remote add origin https://github.com/yourusername/ufc.git
   
   # Configure git credentials (for automation)
   git config user.name "Your Name"
   git config user.email "your.email@example.com"
   
   # Optional: Set up credential caching to avoid password prompts
   git config credential.helper store
   ```

2. **Create logs directory**
   ```bash
   mkdir -p logs
   ```

### Windows Setup (PowerShell Scripts)

#### 1. Configure Script Paths
Edit the script files and update the `PROJECT_DIR` variable:
```powershell
$PROJECT_DIR = "C:\Users\Alvaro\Desktop\ufc"  # Update this path
```

#### 2. Set Execution Policy
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
```

#### 3. Schedule with Task Scheduler

**For Regular Updates (`update_models.ps1`):**
1. Open Task Scheduler (`taskschd.msc`)
2. Create Basic Task
   - Name: "UFC Model Update"
   - Trigger: Daily (or your preferred frequency)
   - Action: Start a program
   - Program: `powershell.exe`
   - Arguments: `-File "C:\Users\Alvaro\Desktop\ufc\scripts\update_models.ps1"`

**For Startup Check (`startup_check.ps1`):**
1. Create Basic Task
   - Name: "UFC Startup Check"
   - Trigger: At startup
   - Action: Start a program
   - Program: `powershell.exe`
   - Arguments: `-File "C:\Users\Alvaro\Desktop\ufc\scripts\startup_check.ps1"`

### Linux/Unix Setup (Bash Scripts)

#### 1. Configure Script Paths
Edit `update_models.sh` and update the path:
```bash
PROJECT_DIR="/path/to/your/ufc"  # Update this path
```

#### 2. Make Scripts Executable
```bash
chmod +x scripts/update_models.sh
```

#### 3. Setup Cron Job
```bash
# Edit crontab
crontab -e

# Add line for daily updates at 2 AM
0 2 * * * /path/to/ufc/scripts/update_models.sh

# Or for updates every 6 hours
0 */6 * * * /path/to/ufc/scripts/update_models.sh
```

## Git Integration Features

### Automatic Commits
The scripts automatically commit and push:
- **Log files** (`logs/model_update.log`, `logs/startup_update.log`)
- **Model files** (if retrained)
- **Output files** (predictions, accuracy reports, etc.)
- **Data files** (if updated with new fights)

### Commit Messages
Automated commits use descriptive messages:
- `"Automated model update: 2025-01-15 14:30:22"`
- `"Startup model check: 2025-01-15 08:15:33"`

### Git Error Handling
- Scripts verify git repository existence
- Check for changes before committing
- Handle network errors gracefully
- Fall back to local commits if push fails
- Continue operation even if git fails

## Monitoring and Logs

### Log Files
- `logs/model_update.log` - Main automation logs
- `logs/startup_update.log` - Startup check logs
- `output/model_results.json` - Latest prediction results

### What Gets Logged
- Pipeline execution start/end times
- Model retraining decisions
- Git operations (add, commit, push)
- Error messages and stack traces
- Resource usage and timeouts

### Sample Log Output
```
[2025-01-15 14:30:15] Starting automated model update and git sync...
[2025-01-15 14:30:16] Running model update pipeline...
[2025-01-15 14:32:45] Model update pipeline completed successfully.
[2025-01-15 14:32:46] Syncing changes to git repository...
[2025-01-15 14:32:46] Git: Adding all changes
[2025-01-15 14:32:47] Git: Adding all changes completed successfully
[2025-01-15 14:32:47] Git: Committing changes
[2025-01-15 14:32:48] Git: Committing changes completed successfully
[2025-01-15 14:32:48] Git: Pushing to remote repository
[2025-01-15 14:32:52] Git: Pushing to remote repository completed successfully
[2025-01-15 14:32:52] Successfully pushed all changes to git repository.
[2025-01-15 14:32:52] Automated update completed successfully with git sync.
```

## Security Considerations

### Git Credentials
- Use SSH keys instead of passwords for git authentication
- Consider using git credential helpers for HTTPS
- Never hardcode credentials in scripts

### File Permissions
```bash
# Secure script files
chmod 750 scripts/*.sh
chmod 750 scripts/*.ps1

# Secure log directory
chmod 755 logs/
```

## Troubleshooting

### Common Issues

1. **Git Authentication Errors**
   ```bash
   # Setup SSH key authentication
   ssh-keygen -t ed25519 -C "your.email@example.com"
   # Add public key to GitHub/GitLab
   ```

2. **PowerShell Execution Policy**
   ```powershell
   # Check current policy
   Get-ExecutionPolicy
   
   # Set to allow scripts
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Path Issues**
   - Verify PROJECT_DIR paths in all scripts
   - Use absolute paths to avoid confusion
   - Check that Python is in system PATH

4. **Resource Limits**
   - Adjust memory limits in scripts if needed
   - Monitor system resources during execution
   - Consider running during off-peak hours

### Debug Mode
Add debug logging by modifying scripts:
```powershell
# PowerShell debug
$DebugPreference = "Continue"
```

```bash
# Bash debug
set -x  # Add to top of script
```

## Customization

### Frequency
- Modify cron schedule or Task Scheduler triggers
- Consider UFC event calendar for optimal timing
- Balance between freshness and resource usage

### Resource Limits
```powershell
# PowerShell - adjust timeout
$MAX_TIMEOUT_MINUTES = 180  # 3 hours
```

```bash
# Bash - adjust memory and timeout
MAX_MEMORY="8G"  # Increase memory limit
NICE_LEVEL="5"   # Higher priority
```

### Notification Settings
Modify `startup_check.ps1` to customize notifications:
```powershell
# Custom notification
[System.Windows.Forms.MessageBox]::Show("Custom message", "Title", "OK", "Information")
```

## Support

For issues or questions:
1. Check log files for error details
2. Verify git repository status manually
3. Test scripts manually before scheduling
4. Review this documentation for configuration details 