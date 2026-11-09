[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string]$Version,
    [string]$Repository,
    [int]$Port = 0,
    [switch]$Check,
    [switch]$Ai,
    [switch]$NonInteractive,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$python = $null
foreach ($candidate in @(@{ Command = 'python'; Args = @() }, @{ Command = 'py'; Args = @('-3') })) {
    if (Get-Command $candidate.Command -ErrorAction SilentlyContinue) {
        $prefix = $candidate.Args
        & $candidate.Command @prefix -c 'import sys; sys.exit(sys.version_info < (3, 10))'
        if ($LASTEXITCODE -eq 0) {
            $python = $candidate.Command
            break
        }
    }
}
if (-not $python -or -not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error 'Install Python 3.10+ and Git, open a new terminal, and rerun setup.'
    exit 1
}

$bootstrap = Join-Path ([IO.Path]::GetTempPath()) ("vita-setup-" + [guid]::NewGuid() + ".py")
try {
    $url = "https://raw.githubusercontent.com/ABDELLAH-Hallou/vita-tree/v$Version/src/vita_tree/setup.py"
    try {
        Invoke-WebRequest -UseBasicParsing -TimeoutSec 30 -Uri $url -OutFile $bootstrap
    } catch {
        Write-Error "Setup download failed. Check your connection and the published version $Version, then retry."
        exit 1
    }
    $options = @('--release', $Version, '--port', "$Port")
    if ($Repository) { $options += @('--repository', $Repository) }
    if ($Check) { $options += '--check' }
    if ($Ai) { $options += '--ai' }
    if ($NonInteractive) { $options += '--non-interactive' }
    if ($NoBrowser) { $options += '--no-browser' }
    & $python @prefix -I $bootstrap @options
    exit $LASTEXITCODE
} finally {
    if (Test-Path -LiteralPath $bootstrap) { Remove-Item -LiteralPath $bootstrap }
}
