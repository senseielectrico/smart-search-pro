"""
Comprehensive Test Suite for Secure Vault System
Tests encryption, steganography, anti-forensics, and UI
"""

import os
import sys
import tempfile
import secrets
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from vault.secure_vault import SecureVault, VaultConfig, SecureMemory
from vault.steganography import SteganographyEngine
from vault.anti_forensics import AntiForensics
from vault.virtual_fs import VirtualFileSystem


def test_vault_creation():
    """Test vault creation and basic operations"""
    print("Testing Vault Creation...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create vault
        config = VaultConfig()
        config.container_path = os.path.join(tmpdir, "test.dll")

        vault = SecureVault(config)

        # Create with password
        password = "TestPassword123!@#"
        decoy_password = "DecoyPassword456$%^"

        assert vault.create_vault(password, decoy_password), "Failed to create vault"
        assert os.path.exists(config.container_path), "Container file not created"

        print("  Vault created successfully")

        # Unlock with main password
        vault2 = SecureVault(config)
        is_main = vault2.unlock_vault(password)
        assert is_main, "Failed to unlock with main password"

        print("  Unlocked with main password")

        # Test file operations
        test_data = b"Secret test data " * 100
        test_path = os.path.join(tmpdir, "test.txt")

        with open(test_path, 'wb') as f:
            f.write(test_data)

        # Add file
        assert vault2.add_file(test_path, "/test.txt"), "Failed to add file"

        # Save vault
        assert vault2.save_vault(), "Failed to save vault"

        print("  File added and vault saved")

        # Lock and re-unlock
        vault2.lock_vault()

        vault3 = SecureVault(config)
        vault3.unlock_vault(password)

        # Extract file
        output_path = os.path.join(tmpdir, "extracted.txt")
        assert vault3.extract_file("/test.txt", output_path), "Failed to extract file"

        with open(output_path, 'rb') as f:
            extracted_data = f.read()

        assert extracted_data == test_data, "Extracted data doesn't match"

        print("  File extracted and verified")

        # Test decoy password
        vault4 = SecureVault(config)
        is_main = vault4.unlock_vault(decoy_password)
        assert not is_main, "Decoy password opened main vault"

        print("  Decoy password works correctly")

    print("PASSED: Vault Creation")


def test_encryption_security():
    """Test encryption security features"""
    print("\nTesting Encryption Security...")

    with tempfile.TemporaryDirectory() as tmpdir:
        config = VaultConfig()
        config.container_path = os.path.join(tmpdir, "secure.dll")

        vault = SecureVault(config)
        password = "StrongPassword!@#123"

        vault.create_vault(password)

        # Test wrong password
        vault2 = SecureVault(config)
        try:
            vault2.unlock_vault("WrongPassword")
            assert False, "Vault opened with wrong password!"
        except ValueError:
            print("  Wrong password rejected correctly")

        # Test file not found
        vault3 = SecureVault(VaultConfig())
        vault3.config.container_path = os.path.join(tmpdir, "nonexistent.dll")
        try:
            vault3.unlock_vault(password)
            assert False, "Opened non-existent vault"
        except FileNotFoundError:
            print("  Non-existent vault handled correctly")

        # Test secure memory clearing
        test_bytes = bytearray(b"sensitive data")
        SecureMemory.clear_bytes(test_bytes)
        assert all(b == 0 for b in test_bytes), "Memory not cleared"

        print("  Secure memory clearing works")

    print("PASSED: Encryption Security")


def test_steganography():
    """Test steganography features"""
    print("\nTesting Steganography...")

    # Skip if PIL not available
    try:
        from PIL import Image
    except ImportError:
        print("  SKIPPED: PIL/Pillow not installed")
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test image
        img = Image.new('RGB', (800, 600), color='blue')
        carrier_path = os.path.join(tmpdir, "carrier.png")
        img.save(carrier_path)

        # Test data
        secret_data = b"This is secret vault data! " * 50

        # Hide in PNG
        output_path = os.path.join(tmpdir, "output.png")
        assert SteganographyEngine.hide_in_png(carrier_path, secret_data, output_path), \
            "Failed to hide data in PNG"

        print("  Data hidden in PNG")

        # Verify carrier integrity
        assert SteganographyEngine.verify_carrier_integrity(carrier_path, output_path), \
            "Carrier integrity compromised"

        print("  Carrier integrity preserved")

        # Extract data
        extracted = SteganographyEngine.extract_from_png(output_path)
        assert extracted == secret_data, "Extracted data doesn't match"

        print("  Data extracted successfully")

        # Test capacity
        capacity = SteganographyEngine.get_carrier_capacity(carrier_path)
        assert capacity > 0, "Failed to calculate capacity"

        print(f"  Carrier capacity: {capacity} bytes")

        # Test auto hide/extract
        auto_output = os.path.join(tmpdir, "auto_output.png")
        assert SteganographyEngine.auto_hide(carrier_path, secret_data, auto_output), \
            "Auto hide failed"

        auto_extracted = SteganographyEngine.auto_extract(auto_output)
        assert auto_extracted == secret_data, "Auto extract failed"

        print("  Auto hide/extract works")

    print("PASSED: Steganography")


def test_anti_forensics():
    """Test anti-forensics features"""
    print("\nTesting Anti-Forensics...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file
        test_file = os.path.join(tmpdir, "test.dat")
        test_data = secrets.token_bytes(1024)

        with open(test_file, 'wb') as f:
            f.write(test_data)

        # Test timestamp randomization
        original_mtime = os.path.getmtime(test_file)
        assert AntiForensics.randomize_timestamps(test_file), "Failed to randomize timestamps"

        new_mtime = os.path.getmtime(test_file)
        assert new_mtime != original_mtime, "Timestamp not changed"

        print("  Timestamp randomization works")

        # Test file blending
        assert AntiForensics.blend_with_system_files(test_file), "Failed to blend file"

        print("  File blending works")

        # Test secure deletion
        assert AntiForensics.secure_delete(test_file, passes=3), "Failed to secure delete"
        assert not os.path.exists(test_file), "File still exists after secure delete"

        print("  Secure deletion works")

        # Test environment detection
        env_info = AntiForensics.get_environment_info()
        assert 'platform' in env_info, "Failed to get environment info"
        assert 'debugger_attached' in env_info, "Missing debugger detection"

        print(f"  Environment: {env_info['platform']}")
        print(f"  Debugger: {env_info['debugger_attached']}")
        print(f"  VM: {env_info['vm_detected']}")

        # Test decoy generation
        decoys = AntiForensics.generate_decoy_files(tmpdir, count=5)
        assert len(decoys) == 5, "Failed to generate decoys"

        for decoy in decoys:
            assert os.path.exists(decoy), f"Decoy not created: {decoy}"

        print(f"  Generated {len(decoys)} decoy files")

    print("PASSED: Anti-Forensics")


def test_virtual_filesystem():
    """Test virtual filesystem"""
    print("\nTesting Virtual Filesystem...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create vault
        config = VaultConfig()
        config.container_path = os.path.join(tmpdir, "vfs.dll")

        vault = SecureVault(config)
        vault.create_vault("password123")
        vault.unlock_vault("password123")

        # Create VFS
        vfs = VirtualFileSystem()
        vfs.mount(vault)

        print("  VFS mounted")

        # Create directories
        assert vfs.mkdir("/documents"), "Failed to create directory"
        assert vfs.mkdir("/documents/work", parents=True), "Failed to create nested directory"

        print("  Directories created")

        # Write files
        test_content = b"Test file content in VFS"
        assert vfs.write_file("/documents/test.txt", test_content), "Failed to write file"

        print("  File written")

        # Read file
        read_content = vfs.read_file("/documents/test.txt")
        assert read_content == test_content, "Read content doesn't match"

        print("  File read successfully")

        # List directory
        files = vfs.list_dir("/documents")
        assert len(files) >= 1, "Failed to list directory"

        print(f"  Listed {len(files)} items")

        # Copy file
        assert vfs.copy("/documents/test.txt", "/documents/test_copy.txt"), "Failed to copy"

        print("  File copied")

        # Move file
        assert vfs.move("/documents/test_copy.txt", "/test_moved.txt"), "Failed to move"

        print("  File moved")

        # Delete file
        assert vfs.delete("/test_moved.txt"), "Failed to delete"

        print("  File deleted")

        # Get info
        info = vfs.get_info("/documents/test.txt")
        assert info is not None, "Failed to get file info"
        assert info.size == len(test_content), "File size mismatch"

        print("  File info retrieved")

        # Test find
        results = vfs.find("*.txt")
        assert len(results) > 0, "Failed to find files"

        print(f"  Found {len(results)} files")

        # Test import/export
        source_dir = os.path.join(tmpdir, "source")
        os.makedirs(source_dir)

        with open(os.path.join(source_dir, "import_test.txt"), 'w') as f:
            f.write("Import test")

        assert vfs.import_tree(source_dir, "/imported"), "Failed to import tree"

        print("  Tree imported")

        export_dir = os.path.join(tmpdir, "export")
        os.makedirs(export_dir)

        assert vfs.export_tree(export_dir, "/imported"), "Failed to export tree"

        print("  Tree exported")

        # Verify export
        exported_file = os.path.join(export_dir, "imported", "import_test.txt")
        assert os.path.exists(exported_file), "Exported file not found"

        # Unmount
        vfs.unmount()

        print("  VFS unmounted")

    print("PASSED: Virtual Filesystem")


def test_password_change():
    """Test password change functionality"""
    print("\nTesting Password Change...")

    with tempfile.TemporaryDirectory() as tmpdir:
        config = VaultConfig()
        config.container_path = os.path.join(tmpdir, "pwchange.dll")

        vault = SecureVault(config)

        old_password = "OldPassword123"
        new_password = "NewPassword456"

        vault.create_vault(old_password)
        vault.unlock_vault(old_password)

        # Add test file
        test_data = b"Password change test"
        test_file = os.path.join(tmpdir, "test.txt")

        with open(test_file, 'wb') as f:
            f.write(test_data)

        vault.add_file(test_file, "/test.txt")
        vault.save_vault()

        # Change password
        assert vault.change_password(old_password, new_password), "Failed to change password"

        print("  Password changed")

        # Lock and unlock with new password
        vault.lock_vault()

        vault2 = SecureVault(config)
        assert vault2.unlock_vault(new_password), "Failed to unlock with new password"

        print("  Unlocked with new password")

        # Verify old password doesn't work
        vault3 = SecureVault(config)
        try:
            vault3.unlock_vault(old_password)
            assert False, "Old password still works!"
        except ValueError:
            print("  Old password rejected")

        # Verify file intact
        output = os.path.join(tmpdir, "output.txt")
        vault2.extract_file("/test.txt", output)

        with open(output, 'rb') as f:
            assert f.read() == test_data, "File corrupted after password change"

        print("  File intact after password change")

    print("PASSED: Password Change")


def test_vault_statistics():
    """Test vault statistics"""
    print("\nTesting Vault Statistics...")

    with tempfile.TemporaryDirectory() as tmpdir:
        config = VaultConfig()
        config.container_path = os.path.join(tmpdir, "stats.dll")

        vault = SecureVault(config)
        vault.create_vault("password")
        vault.unlock_vault("password")

        # Add multiple files
        for i in range(5):
            test_file = os.path.join(tmpdir, f"test{i}.txt")
            with open(test_file, 'wb') as f:
                f.write(f"Test file {i}".encode() * 100)

            vault.add_file(test_file, f"/test{i}.txt")

        vault.save_vault()

        # Get statistics
        stats = vault.get_vault_stats()

        assert stats['file_count'] == 5, "Wrong file count"
        assert stats['total_size'] > 0, "Total size is zero"
        assert 'container_path' in stats, "Missing container path"

        print(f"  Files: {stats['file_count']}")
        print(f"  Size: {stats['total_size']} bytes")

    print("PASSED: Vault Statistics")


def run_all_tests():
    """Run all vault system tests"""
    print("=" * 60)
    print("SECURE VAULT SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    tests = [
        test_vault_creation,
        test_encryption_security,
        test_steganography,
        test_anti_forensics,
        test_virtual_filesystem,
        test_password_change,
        test_vault_statistics,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\nFAILED: {test_func.__name__}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
