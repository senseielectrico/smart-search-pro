# Everything SDK Setup Guide

## Current Status

Everything.exe is installed at: `C:\Program Files\Everything\Everything.exe`

However, the Everything SDK DLL is **NOT installed**. The SDK DLL is required for programmatic access.

## Installation Steps

### Option 1: Download Everything SDK (Recommended)

1. Download the Everything SDK from:
   https://www.voidtools.com/support/everything/sdk/

2. Extract the SDK archive and copy the appropriate DLL:
   - For 64-bit Python: Copy `Everything64.dll` to `C:\Program Files\Everything\`
   - For 32-bit Python: Copy `Everything32.dll` to `C:\Program Files\Everything\`

3. Check your Python architecture:
   ```powershell
   python -c "import struct; print(f'{struct.calcsize(\"P\")*8}-bit')"
   ```

### Option 2: Automated PowerShell Installation

Run this PowerShell script as Administrator:

```powershell
# Download and install Everything SDK
$sdkUrl = "https://www.voidtools.com/Everything-SDK.zip"
$tempPath = "$env:TEMP\Everything-SDK.zip"
$extractPath = "$env:TEMP\Everything-SDK"
$installPath = "C:\Program Files\Everything"

# Download SDK
Write-Host "Downloading Everything SDK..."
Invoke-WebRequest -Uri $sdkUrl -OutFile $tempPath

# Extract
Write-Host "Extracting SDK..."
Expand-Archive -Path $tempPath -DestinationPath $extractPath -Force

# Copy DLL (try both 32 and 64 bit)
if (Test-Path "$extractPath\dll\Everything64.dll") {
    Copy-Item "$extractPath\dll\Everything64.dll" -Destination $installPath -Force
    Write-Host "Installed Everything64.dll"
}
if (Test-Path "$extractPath\dll\Everything32.dll") {
    Copy-Item "$extractPath\dll\Everything32.dll" -Destination $installPath -Force
    Write-Host "Installed Everything32.dll"
}

# Cleanup
Remove-Item $tempPath -Force
Remove-Item $extractPath -Recurse -Force

Write-Host "Everything SDK installed successfully!"
```

### Option 3: Use Fallback (Current Mode)

The system is currently using **Windows Search fallback mode**. This works but is slower than Everything SDK.

No action needed if acceptable performance.

## Verification

After installing the SDK DLL, verify with:

```bash
python test_everything.py
```

Look for:
```
Everything SDK initialized: True
Using fallback: False
```

## Features Available

### With Everything SDK (DLL installed):
- Instant search (< 1ms for most queries)
- Index of all files on NTFS drives
- Advanced query syntax
- Regex support
- Real-time updates
- Low memory footprint

### With Windows Search Fallback (Current):
- PowerShell-based file search
- Slower search (seconds vs milliseconds)
- Limited to indexed locations
- Basic wildcard support
- No real-time updates

## Query Examples

Once SDK is installed, you can use advanced queries:

```python
from search.everything_sdk import get_everything_instance, EverythingSort

sdk = get_everything_instance()

# Basic search
results = sdk.search("*.py", max_results=100)

# Extension filter
results = sdk.search("ext:py;txt;md")

# Size filter
results = sdk.search("size:>10mb")

# Date filter
results = sdk.search("dm:today")  # modified today

# Regex
results = sdk.search("regex:test_.*\.py$", regex=True)

# Folder only
results = sdk.search("folder:", max_results=50)

# Path matching
results = sdk.search("c:\\projects\\ *.py", match_path=True)

# Sorted
results = sdk.search(
    "*.log",
    sort=EverythingSort.DATE_MODIFIED_DESCENDING
)

# Async with callback
def on_results(results):
    print(f"Found {len(results)} files")

sdk.search_async("*.pdf", callback=on_results)
```

## Troubleshooting

### DLL Not Found
- Verify DLL is in `C:\Program Files\Everything\`
- Check Python architecture matches DLL (32-bit vs 64-bit)
- Ensure Everything.exe is running
- Check file permissions

### Everything Not Running
The SDK will automatically try to start Everything.exe if installed.

Manually start with:
```powershell
Start-Process "C:\Program Files\Everything\Everything.exe" -ArgumentList "-startup"
```

### Database Not Loaded
Wait a few seconds after starting Everything for the database to load.

Check status:
```python
sdk = get_everything_instance()
print(sdk.is_available)  # Should be True
```

### Performance Issues with Fallback
The Windows Search fallback is significantly slower. Consider installing the SDK DLL for optimal performance.

## Architecture Decision

The implementation includes both:
1. **Primary**: Everything SDK via ctypes (fastest)
2. **Fallback**: Windows Search via PowerShell (slower but works without SDK)

This ensures the application always works, even without Everything SDK installed.

## Next Steps

1. Install Everything SDK DLL (see Option 1 or 2 above)
2. Run `python test_everything.py` to verify
3. Integrate with Smart Search Pro UI
4. Enjoy instant file search!

## Additional Resources

- Everything Homepage: https://www.voidtools.com/
- Everything SDK: https://www.voidtools.com/support/everything/sdk/
- Everything Search Syntax: https://www.voidtools.com/support/everything/searching/
