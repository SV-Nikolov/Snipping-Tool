param(
    [switch]$Clean,
    [switch]$WithConsole,
    [string]$Version = "",
    [switch]$ListChanges,
    [switch]$SkipVenv
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-IfExists($cmd, $args) {
    try { & $cmd @args } catch { throw }
}

function Stop-RunningExe {
    try {
        Get-Process -Name 'SnippingToolPy' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    } catch { }
}

function Remove-PathRobust([string]$path) {
    for ($i = 0; $i -lt 3; $i++) {
        try {
            if (Test-Path $path) {
                Remove-Item -Recurse -Force -ErrorAction Stop $path
            }
            break
        } catch {
            # Attempt to unlock and retry
            Stop-RunningExe
            Start-Sleep -Milliseconds 300
        }
    }
}

function Get-GitPath {
    $git = (Get-Command git -ErrorAction SilentlyContinue).Source
    return $git
}

function Get-RepoRoot {
    return (Split-Path $PSScriptRoot -Parent)
}

function Get-CurrentSha {
    $git = Get-GitPath
    if (-not $git) { return $null }
    Push-Location (Get-RepoRoot)
    try { (& $git rev-parse --short HEAD).Trim() } catch { $null } finally { Pop-Location }
}

function Show-ChangesSinceLastBuild {
    $git = Get-GitPath
    if (-not $git) { Write-Host "git not found; skipping change summary"; return }
    $repo = Get-RepoRoot
    $marker = Join-Path $PSScriptRoot '.last_build.sha'
    $prev = if (Test-Path $marker) { (Get-Content $marker -ErrorAction SilentlyContinue | Select-Object -First 1).Trim() } else { $null }
    Push-Location $repo
    try {
        if ($prev) {
            Write-Host "Changes since ${prev}:" -ForegroundColor Cyan
            & $git --no-pager diff --name-status $prev..HEAD | ForEach-Object { Write-Host $_ }
        } else {
            Write-Host "Untracked/modified files:" -ForegroundColor Cyan
            & $git --no-pager status --porcelain | ForEach-Object { Write-Host $_ }
        }
    } finally { Pop-Location }
}

function Ensure-Venv {
    if ($SkipVenv) { return }
    if (-not (Test-Path (Join-Path $PSScriptRoot '.venv'))) {
        Write-Host "Creating virtual environment..."
        py -3 -m venv (Join-Path $PSScriptRoot '.venv')
    }
    Write-Host "Activating venv and installing dependencies..."
    . (Join-Path $PSScriptRoot '.venv\Scripts\Activate.ps1')
    pip install --upgrade pip
    pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
    pip install pyinstaller pywin32
}

function Clean-Artifacts {
    Write-Host "Cleaning build artifacts..."
    Stop-RunningExe
    Remove-PathRobust (Join-Path $PSScriptRoot 'build')
    Remove-PathRobust (Join-Path $PSScriptRoot 'dist')
    Get-ChildItem -Path $PSScriptRoot -Filter '*.spec' -ErrorAction SilentlyContinue | ForEach-Object { 
        try { Remove-Item -Force -ErrorAction Stop $_.FullName } catch { Start-Sleep -Milliseconds 200; try { Remove-Item -Force -ErrorAction SilentlyContinue $_.FullName } catch { } }
    }
}

function Build-Exe {
    $name = 'SnippingToolPy'
    $entry = Join-Path $PSScriptRoot 'snipping_tool\app.py'
    $args = @(
        '--onefile', '--name', $name,
        '--hidden-import','snipping_tool.core.capture',
        '--hidden-import','snipping_tool.core.storage',
        '--hidden-import','snipping_tool.core.logger',
        '--hidden-import','PIL.ImageTk'
    )
    if (-not $WithConsole) { $args += '--noconsole' }
    if ($Version -and $Version.Trim().Length -gt 0) {
        Write-Host "Embedding version: $Version"
        # Simple approach: pass version as environment for optional runtime display (not file metadata)
        $env:APP_VERSION = $Version
    }
    Write-Host "Building standalone EXE with PyInstaller..."
    Stop-RunningExe
    pyinstaller @args $entry
    if ($LASTEXITCODE -ne 0) {
        Write-Error "PyInstaller failed with exit code $LASTEXITCODE. Ensure the app isn't running and check the output above."
        return $null
    }
    $exePath = Join-Path $PSScriptRoot "dist\$name.exe"
    if (Test-Path $exePath) {
        $exe = Resolve-Path $exePath
        Write-Host "Build complete. EXE at: $exe"
        return $exe
    } else {
        Write-Warning "Build finished but EXE not found at: $exePath. Check PyInstaller output above for errors."
        return $null
    }
}

Push-Location $PSScriptRoot
try {
    if ($Clean) { Clean-Artifacts }
    if ($ListChanges) { Show-ChangesSinceLastBuild }
    Ensure-Venv
    $exe = Build-Exe
    $sha = Get-CurrentSha
    if ($sha) {
        Set-Content -Path (Join-Path $PSScriptRoot '.last_build.sha') -Value $sha -Encoding ascii
        Write-Host "Recorded last build commit: $sha"
    }
}
finally {
    Pop-Location
}
