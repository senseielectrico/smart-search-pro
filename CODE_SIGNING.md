# Code Signing Instructions for Smart Search Pro

## Why Code Signing?

Code signing is the most effective way to prevent antivirus false positives. A properly signed executable:
- Tells Windows and antivirus software that the code comes from a verified publisher
- Prevents "Unknown Publisher" warnings
- Builds trust with users
- Reduces SmartScreen warnings

## Options for Code Signing

### Option 1: Self-Signed Certificate (Free, Development Only)

```powershell
# Create a self-signed certificate
$cert = New-SelfSignedCertificate -Type CodeSigning -Subject "CN=Smart Search Pro" -KeyAlgorithm RSA -KeyLength 2048 -CertStoreLocation "Cert:\CurrentUser\My" -NotAfter (Get-Date).AddYears(3)

# Export the certificate
Export-PfxCertificate -Cert $cert -FilePath "SmartSearchPro.pfx" -Password (ConvertTo-SecureString -String "YourPassword" -Force -AsPlainText)

# Sign the executable
Set-AuthenticodeSignature -FilePath "release\SmartSearchPro\SmartSearchPro.exe" -Certificate $cert -TimestampServer "http://timestamp.digicert.com"
```

**Note**: Self-signed certificates still show warnings. Only useful for internal testing.

### Option 2: Free Code Signing with SignPath (Open Source Projects)

1. Go to https://signpath.io/
2. Apply for free open source signing
3. Submit your GitHub repository for verification
4. Use their CI/CD integration to sign releases

### Option 3: Commercial Code Signing Certificate ($200-500/year)

Recommended providers:
- **Sectigo** (formerly Comodo): ~$200/year
- **DigiCert**: ~$400/year
- **GlobalSign**: ~$300/year

Process:
1. Purchase certificate from provider
2. Complete identity verification (business or individual)
3. Receive certificate file (.pfx)
4. Sign with SignTool:

```cmd
# Sign the executable
signtool sign /f "certificate.pfx" /p "password" /tr "http://timestamp.digicert.com" /td sha256 /fd sha256 "SmartSearchPro.exe"

# Verify signature
signtool verify /pa "SmartSearchPro.exe"
```

### Option 4: Azure Trusted Signing (Best for Organizations)

Microsoft's cloud-based signing service:
1. Create Azure account
2. Set up Trusted Signing resource
3. Complete identity validation
4. Sign using Azure CLI or CI/CD

```powershell
# Install Azure CLI extension
az extension add --name trustedsigning

# Sign
az trustedsigning sign --account-name "YourAccount" --certificate-profile "YourProfile" --files "SmartSearchPro.exe"
```

## Additional AV False Positive Prevention

Even without signing, these steps help reduce false positives:

1. **Use --noupx** in PyInstaller (already implemented)
2. **Include proper Windows manifest** (already implemented)
3. **Use detailed version information** (already implemented)
4. **Submit to antivirus vendors**:
   - Microsoft: https://www.microsoft.com/wdsi/filesubmission
   - Avast/AVG: https://www.avast.com/false-positive-file-form.php
   - ESET: https://support.eset.com/kb141/
   - Norton: https://submit.symantec.com/false_positive/
   - Kaspersky: https://opentip.kaspersky.com/

5. **VirusTotal submission**: Upload to https://www.virustotal.com and request re-analysis after false positive reports

## Automated Build with Signing

Update `build_release.py` to include signing:

```python
def sign_executable(exe_path: Path, pfx_path: Path, password: str):
    """Sign executable with code signing certificate"""
    import subprocess

    # Find signtool
    signtool = r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"

    cmd = [
        signtool, "sign",
        "/f", str(pfx_path),
        "/p", password,
        "/tr", "http://timestamp.digicert.com",
        "/td", "sha256",
        "/fd", "sha256",
        str(exe_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0
```

## Resources

- [Microsoft Code Signing Best Practices](https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools)
- [PyInstaller Code Signing](https://pyinstaller.org/en/stable/feature-notes.html#windows)
- [SignPath Documentation](https://docs.signpath.io/)
