# TaxBot Windows Task Scheduler Setup Script
# This script sets up automated daily scraping via Windows Task Scheduler

param(
    [string]$ProjectPath = (Split-Path -Parent $PSScriptRoot),
    [string]$Time = "06:00"
)

Write-Host "TaxBot Windows Task Setup" -ForegroundColor Blue
Write-Host "=========================" -ForegroundColor Blue

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "This script requires administrator privileges" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator" -ForegroundColor Yellow
    exit 1
}

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
$venvPath = Join-Path $ProjectPath "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    Set-Location $ProjectPath
    python -m venv venv
    & "$venvPath\Scripts\Activate.ps1"
    pip install -r requirements.txt
} else {
    Write-Host "Virtual environment found" -ForegroundColor Green
}

# Check if .env file exists
$envPath = Join-Path $ProjectPath ".env"
if (-not (Test-Path $envPath)) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item (Join-Path $ProjectPath ".env.example") $envPath
    Write-Host "Please edit .env file with your configuration" -ForegroundColor Yellow
}

# Create logs directory
$logsPath = Join-Path $ProjectPath "logs"
if (-not (Test-Path $logsPath)) {
    New-Item -ItemType Directory -Path $logsPath -Force
}

# Create PowerShell script for the task
$taskScriptPath = Join-Path $ProjectPath "scripts\run_taxbot.ps1"
$taskScriptContent = @"
# TaxBot Task Runner
Set-Location '$ProjectPath'
& '$venvPath\Scripts\Activate.ps1'
python -m taxbot.cli.commands scrape >> logs\task.log 2>&1
"@

Set-Content -Path $taskScriptPath -Value $taskScriptContent -Encoding UTF8

# Create scheduled task
$taskName = "TaxBot Daily Scraping"
$taskDescription = "Automated daily scraping of DIAN concepts"

# Remove existing task if it exists
try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
} catch {
    # Task doesn't exist, that's fine
}

# Create new task
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$taskScriptPath`""
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description $taskDescription

Write-Host "Scheduled task created successfully" -ForegroundColor Green
Write-Host "Task Name: $taskName" -ForegroundColor Cyan
Write-Host "Schedule: Daily at $Time" -ForegroundColor Cyan
Write-Host "Script: $taskScriptPath" -ForegroundColor Cyan

# Test the setup
Write-Host "Testing setup..." -ForegroundColor Blue
Set-Location $ProjectPath
& "$venvPath\Scripts\Activate.ps1"

# Test configuration
Write-Host "Testing configuration..."
python -c "
from taxbot.core.config import get_settings
from taxbot.core.logging import setup_logging
setup_logging()
settings = get_settings()
print(f'Data directory: {settings.data_dir}')
print(f'Ollama model: {settings.ollama_model}')
print(f'Email configured: {bool(settings.email_sender)}')
"

Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your configuration"
Write-Host "2. Test email configuration: python -m taxbot.cli.commands test-email"
Write-Host "3. Test Ollama: python -m taxbot.cli.commands test-ollama"
Write-Host "4. Run manual scraping: python -m taxbot.cli.commands scrape"
Write-Host "5. Check task logs: Get-Content logs\task.log"
Write-Host ""
Write-Host "To remove the scheduled task:"
Write-Host "Unregister-ScheduledTask -TaskName '$taskName'"
