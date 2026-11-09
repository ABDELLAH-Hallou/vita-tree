# Vita Tree Windows Setup Helper
# Can be run from PowerShell or CMD:
# powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
[CmdletBinding()]
param(
    [switch]$Check,
    [switch]$Demo,
    [switch]$NonInteractive
)

$ErrorActionPreference = 'Stop'

Write-Host "Vita Tree Setup (Windows)" -ForegroundColor Cyan
Write-Host "========================="

# 1. Check Python
$pythonCmd = $null
foreach ($cmd in @('python', 'py -3', 'python3')) {
    try {
        $ver = & $cmd.Split(' ')[0] $cmd.Split(' ')[1..($cmd.Split(' ').Length-1)] -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($LASTEXITCODE -eq 0 -and [version]$ver -ge [version]'3.10') {
            $pythonCmd = $cmd
            Write-Host "Found compatible Python: $ver ($cmd)" -ForegroundColor Green
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "Compatible Python (3.10+) not found on PATH." -ForegroundColor Yellow
    Write-Host "Please install Python 3.10 or newer from https://www.python.org/downloads/ or via winget: winget install Python.Python.3.12"
    if ($Check) { exit 1 }
}

# 2. Check Git
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if ($gitCmd) {
    Write-Host "Found Git: $($gitCmd.Source)" -ForegroundColor Green
} else {
    Write-Host "Git not found on PATH. Git is required to manage CV versions and branches." -ForegroundColor Yellow
    Write-Host "Install Git from https://git-scm.com/download/win or via winget: winget install Git.Git"
    if ($Check) { exit 1 }
}

# 3. Check TeX (optional)
$texCmd = Get-Command pdflatex -ErrorAction SilentlyContinue
if ($texCmd) {
    Write-Host "Found TeX engine: $($texCmd.Source)" -ForegroundColor Green
} else {
    Write-Host "TeX engine not found. Note: TeX is only required for PDF previews, not for editing/branching." -ForegroundColor DarkGray
    Write-Host "To enable PDF previews, install MiKTeX: winget install MiKTeX.MiKTeX" -ForegroundColor DarkGray
}

if ($Check) {
    if ($pythonCmd -and $gitCmd) { exit 0 } else { exit 1 }
}

# 4. Launch setup or demo via python module
$setupArgs = @()
if ($Demo) { $setupArgs += '--demo' }
if ($NonInteractive) { $setupArgs += '--non-interactive' }

if ($pythonCmd) {
    & $pythonCmd.Split(' ')[0] $pythonCmd.Split(' ')[1..($pythonCmd.Split(' ').Length-1)] -m vita_tree.setup @setupArgs
    exit $LASTEXITCODE
}
