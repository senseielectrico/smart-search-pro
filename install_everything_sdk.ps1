# Everything SDK Installer
# Automatically downloads and installs Everything SDK DLL

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Everything SDK Installer for Smart Search Pro" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "WARNING: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "Some operations may fail. Consider running as Administrator." -ForegroundColor Yellow
    Write-Host ""
}

# Configuration
$sdkUrl = "https://www.voidtools.com/Everything-SDK.zip"
$tempPath = "$env:TEMP\Everything-SDK-$(Get-Random).zip"
$extractPath = "$env:TEMP\Everything-SDK-$(Get-Random)"
$installPath = "C:\Program Files\Everything"

# Verify Everything is installed
Write-Host "Step 1: Checking Everything installation..." -ForegroundColor Green
if (-not (Test-Path "$installPath\Everything.exe")) {
    Write-Host "ERROR: Everything.exe not found at $installPath" -ForegroundColor Red
    Write-Host "Please install Everything first from: https://www.voidtools.com/" -ForegroundColor Yellow
    exit 1
}
Write-Host "  Everything.exe found: $installPath\Everything.exe" -ForegroundColor White

# Check if SDK already installed
Write-Host ""
Write-Host "Step 2: Checking for existing SDK DLL..." -ForegroundColor Green
$dll64Exists = Test-Path "$installPath\Everything64.dll"
$dll32Exists = Test-Path "$installPath\Everything32.dll"

if ($dll64Exists -or $dll32Exists) {
    if (-not $Force) {
        Write-Host "  SDK DLL already installed:" -ForegroundColor Yellow
        if ($dll64Exists) { Write-Host "    - Everything64.dll" -ForegroundColor White }
        if ($dll32Exists) { Write-Host "    - Everything32.dll" -ForegroundColor White }

        $response = Read-Host "  Reinstall anyway? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Host "  Installation cancelled." -ForegroundColor Yellow
            exit 0
        }
    } else {
        Write-Host "  Forcing reinstall..." -ForegroundColor Yellow
    }
}

# Check Python architecture
Write-Host ""
Write-Host "Step 3: Detecting Python architecture..." -ForegroundColor Green
$pythonArch = python -c "import struct; print(struct.calcsize('P')*8)"
Write-Host "  Python architecture: $pythonArch-bit" -ForegroundColor White

# Download SDK
Write-Host ""
Write-Host "Step 4: Downloading Everything SDK..." -ForegroundColor Green
Write-Host "  URL: $sdkUrl" -ForegroundColor White

try {
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $sdkUrl -OutFile $tempPath -UseBasicParsing
    $fileSize = (Get-Item $tempPath).Length
    Write-Host "  Downloaded: $([math]::Round($fileSize/1KB, 2)) KB" -ForegroundColor White
} catch {
    Write-Host "ERROR: Failed to download SDK" -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    exit 1
}

# Extract SDK
Write-Host ""
Write-Host "Step 5: Extracting SDK..." -ForegroundColor Green
try {
    Expand-Archive -Path $tempPath -DestinationPath $extractPath -Force
    Write-Host "  Extracted to: $extractPath" -ForegroundColor White
} catch {
    Write-Host "ERROR: Failed to extract SDK" -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    exit 1
}

# Find DLL files
Write-Host ""
Write-Host "Step 6: Locating DLL files..." -ForegroundColor Green
$dllFiles = Get-ChildItem -Path $extractPath -Recurse -Filter "Everything*.dll" -ErrorAction SilentlyContinue

if ($dllFiles.Count -eq 0) {
    Write-Host "ERROR: No DLL files found in SDK archive" -ForegroundColor Red
    exit 1
}

Write-Host "  Found DLL files:" -ForegroundColor White
foreach ($dll in $dllFiles) {
    Write-Host "    - $($dll.Name) ($([math]::Round($dll.Length/1KB, 2)) KB)" -ForegroundColor White
}

# Copy DLL files
Write-Host ""
Write-Host "Step 7: Installing DLL files..." -ForegroundColor Green

$installed = @()
$failed = @()

foreach ($dll in $dllFiles) {
    $destPath = Join-Path $installPath $dll.Name

    try {
        Copy-Item $dll.FullName -Destination $destPath -Force
        Write-Host "  Installed: $($dll.Name)" -ForegroundColor Green
        $installed += $dll.Name
    } catch {
        Write-Host "  FAILED: $($dll.Name) - $_" -ForegroundColor Red
        $failed += $dll.Name
    }
}

# Cleanup
Write-Host ""
Write-Host "Step 8: Cleaning up temporary files..." -ForegroundColor Green
Remove-Item $tempPath -Force -ErrorAction SilentlyContinue
Remove-Item $extractPath -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "  Temporary files removed" -ForegroundColor White

# Summary
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Installation Summary" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

if ($installed.Count -gt 0) {
    Write-Host "Successfully installed:" -ForegroundColor Green
    foreach ($name in $installed) {
        Write-Host "  + $name" -ForegroundColor White
    }
}

if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Host "Failed to install:" -ForegroundColor Red
    foreach ($name in $failed) {
        Write-Host "  - $name" -ForegroundColor White
    }
}

# Verify installation
Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Green

$dll64Path = "$installPath\Everything64.dll"
$dll32Path = "$installPath\Everything32.dll"

$dll64OK = Test-Path $dll64Path
$dll32OK = Test-Path $dll32Path

if ($pythonArch -eq "64" -and $dll64OK) {
    Write-Host "  Everything64.dll: OK (matches Python architecture)" -ForegroundColor Green
} elseif ($pythonArch -eq "32" -and $dll32OK) {
    Write-Host "  Everything32.dll: OK (matches Python architecture)" -ForegroundColor Green
} elseif ($dll64OK -or $dll32OK) {
    Write-Host "  DLL installed but may not match Python architecture" -ForegroundColor Yellow
} else {
    Write-Host "  No DLL installed successfully" -ForegroundColor Red
}

# Check if Everything is running
Write-Host ""
Write-Host "Checking Everything service status..." -ForegroundColor Green
$everythingProcess = Get-Process -Name "Everything" -ErrorAction SilentlyContinue

if ($everythingProcess) {
    Write-Host "  Everything.exe is running (PID: $($everythingProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "  Everything.exe is NOT running" -ForegroundColor Yellow
    Write-Host "  Starting Everything..." -ForegroundColor Green

    try {
        Start-Process "$installPath\Everything.exe" -ArgumentList "-startup" -WindowStyle Hidden
        Start-Sleep -Seconds 2
        Write-Host "  Everything started successfully" -ForegroundColor Green
    } catch {
        Write-Host "  Failed to start Everything: $_" -ForegroundColor Red
    }
}

# Final instructions
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Test the SDK installation:" -ForegroundColor White
Write-Host "   cd 'C:\Users\ramos\.local\bin\smart_search'" -ForegroundColor Cyan
Write-Host "   python test_everything.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Look for these indicators:" -ForegroundColor White
Write-Host "   Everything SDK initialized: True" -ForegroundColor Green
Write-Host "   Using fallback: False" -ForegroundColor Green
Write-Host ""
Write-Host "3. If test fails:" -ForegroundColor White
Write-Host "   - Ensure Everything.exe is running" -ForegroundColor Yellow
Write-Host "   - Check DLL matches Python architecture ($pythonArch-bit)" -ForegroundColor Yellow
Write-Host "   - Try running as Administrator" -ForegroundColor Yellow
Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host ""
