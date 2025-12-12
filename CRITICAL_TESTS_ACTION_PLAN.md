# Critical Tests Action Plan - Smart Search Pro

**Priority**: URGENT
**Timeline**: 1-2 weeks
**Objective**: Achieve minimum 85% coverage on critical paths before production

---

## Phase 1: BLOCKERS (Must Fix This Week)

### Task 1.1: Vault Security Test Suite (CRITICAL) - 16 hours

**Status**: ZERO COVERAGE
**Risk**: CRITICAL - Security vulnerability
**Priority**: P0

**Tests to Implement**:

```python
# tests/test_vault_security.py

class TestVaultEncryption:
    """Critical encryption/decryption tests"""

    def test_encrypt_decrypt_roundtrip_success(self):
        """Encrypt file and decrypt back to original"""
        # Test: file → encrypt → decrypt → verify identical

    def test_encryption_preserves_file_size_metadata(self):
        """Ensure metadata is preserved"""

    def test_decrypt_with_wrong_password_fails(self):
        """Wrong password should fail gracefully"""

    def test_encrypt_large_file_1gb(self):
        """Performance test with 1GB file"""

    def test_encrypt_file_already_encrypted(self):
        """Handle double encryption scenario"""

class TestVaultPasswordSecurity:
    """Password validation and strength tests"""

    def test_weak_password_rejected(self):
        """Passwords < 8 chars rejected"""

    def test_password_strength_validation(self):
        """Validate password complexity"""

    def test_password_with_special_characters(self):
        """Support special chars in password"""

class TestVaultSecureDeletion:
    """Anti-forensic secure deletion tests"""

    def test_secure_delete_overwrites_data(self):
        """Verify data is overwritten"""

    def test_secure_delete_removes_metadata(self):
        """Ensure metadata is cleared"""

class TestVaultIntegrity:
    """File integrity and corruption detection"""

    def test_corrupted_encrypted_file_detected(self):
        """Detect file corruption"""

    def test_tampered_file_rejected(self):
        """Reject tampered encrypted files"""

    def test_key_derivation_performance(self):
        """Key derivation should be fast enough"""

class TestVaultConcurrency:
    """Concurrent vault operations"""

    def test_concurrent_encrypt_operations(self):
        """Multiple files encrypted in parallel"""

    def test_vault_database_thread_safety(self):
        """Database access is thread-safe"""
```

**Implementation Checklist**:
- [ ] Create `tests/test_vault_security.py`
- [ ] Create fixtures for test files (small, medium, large)
- [ ] Create password fixtures (weak, strong, special chars)
- [ ] Mock encryption for fast tests
- [ ] Add real encryption tests (marked @slow)
- [ ] Test secure deletion verification
- [ ] Test key derivation
- [ ] Test concurrent operations
- [ ] Document vault security requirements
- [ ] Add vault tests to CI/CD

**Acceptance Criteria**:
- All 15 tests passing
- Coverage: 95%+ on vault module
- Performance: Encrypt/decrypt 1GB file < 10 seconds
- Security: No sensitive data in logs

---

### Task 1.2: Everything SDK Integration Tests - 12 hours

**Status**: NOT TESTED
**Risk**: HIGH - Core functionality dependency
**Priority**: P0

**Tests to Implement**:

```python
# tests/test_everything_integration.py

class TestEverythingSDKAvailability:
    """SDK availability and fallback tests"""

    def test_sdk_initialization_when_available(self):
        """Initialize SDK when Everything installed"""

    def test_sdk_not_available_fallback_graceful(self):
        """Graceful fallback when SDK missing"""

    def test_everything_service_not_running(self):
        """Handle service not running scenario"""

class TestEverythingSearchBasics:
    """Basic search functionality"""

    @pytest.mark.skipif(not HAS_EVERYTHING, reason="Everything SDK not available")
    def test_search_simple_query(self):
        """Search for simple filename"""

    def test_search_with_wildcards(self):
        """Search with * and ? wildcards"""

    def test_search_with_regex(self):
        """Search with regex pattern"""

class TestEverythingSearchPerformance:
    """Performance and scalability tests"""

    def test_search_returns_within_1_second(self):
        """Search should be fast (<1s for 10k results)"""

    def test_search_handles_1_million_results(self):
        """Handle very large result sets"""

    def test_search_cancellation_responsive(self):
        """Cancel search within 100ms"""

class TestEverythingSearchEdgeCases:
    """Edge cases and error handling"""

    def test_search_unicode_filenames(self):
        """Handle Unicode (Chinese, Arabic, Emoji)"""

    def test_search_network_paths(self):
        """Search UNC paths \\\\server\\share"""

    def test_search_long_paths(self):
        """Paths > MAX_PATH (260 chars)"""

    def test_search_during_database_update(self):
        """Search while Everything is indexing"""
```

**Implementation Checklist**:
- [ ] Create `tests/test_everything_integration.py`
- [ ] Create mock Everything SDK for CI
- [ ] Add skip decorators for missing SDK
- [ ] Test basic search queries
- [ ] Test wildcard and regex patterns
- [ ] Test performance (< 1s response)
- [ ] Test Unicode filenames
- [ ] Test UNC network paths
- [ ] Test cancellation
- [ ] Add performance benchmarks
- [ ] Document Everything SDK requirements

**Acceptance Criteria**:
- All 12 tests passing
- Tests work without SDK (mocked)
- Real tests work with SDK
- Performance: <1s for 10k results
- Graceful degradation when SDK missing

---

### Task 1.3: Fix Failing Tests - 4 hours

**Status**: 8 tests failing
**Risk**: MEDIUM - Existing functionality broken
**Priority**: P0

**Fixes Required**:

1. **OperationManager Import Error** (10 minutes)
   ```python
   # tests/test_comprehensive.py - Line ~600
   # WRONG: from operations.manager import OperationManager
   # RIGHT: from operations.manager import OperationsManager
   ```

2. **Export API Tests** (1 hour)
   ```python
   # tests/test_comprehensive.py - Lines 997-1039
   # Issue: API signature mismatch
   # Fix: Check actual export API and update tests
   ```

3. **Database Transaction Rollback** (30 minutes)
   ```python
   # tests/test_comprehensive.py - Line 250-266
   # Issue: Wrong exception type
   # Fix: Use correct exception from core.exceptions
   ```

4. **Quick Hash Test** (30 minutes)
   ```python
   # tests/test_comprehensive.py - Line 818-836
   # Issue: Small file has same quick and full hash
   # Fix: Increase test file size to >20KB
   ```

5. **Signal Connection Tests** (1 hour)
   ```python
   # tests/test_comprehensive.py - Line 912-940
   # Issue: Mock signals don't emit properly
   # Fix: Properly mock PyQt6 signals or skip
   ```

6. **Duplicate Flow Test** (30 minutes)
   ```python
   # tests/test_comprehensive.py - Line 968-991
   # Issue: Method name mismatch
   # Fix: Use correct DuplicateGroup API
   ```

**Implementation Checklist**:
- [ ] Fix OperationManager import
- [ ] Fix Export API tests
- [ ] Fix transaction rollback exception
- [ ] Fix quick hash test file size
- [ ] Fix or skip signal tests
- [ ] Fix duplicate flow API
- [ ] Run full test suite
- [ ] Verify all fixes

**Acceptance Criteria**:
- All 53 tests in test_comprehensive.py passing
- No import errors
- No API mismatches
- Coverage maintained or improved

---

## Phase 2: HIGH PRIORITY (Next Week)

### Task 2.1: File Operations Reliability Suite - 12 hours

**Status**: INCOMPLETE
**Risk**: HIGH - Data corruption potential
**Priority**: P1

**Tests to Implement**:

```python
# tests/test_operations_reliability.py

class TestLargeFileOperations:
    """Large file handling tests"""

    def test_copy_file_1gb_success(self):
        """Copy 1GB file successfully"""

    def test_copy_file_10gb_progress_tracking(self):
        """10GB file with accurate progress"""

    def test_move_large_file_across_drives(self):
        """Move large file between filesystems"""

class TestErrorHandling:
    """Error scenarios and recovery"""

    def test_copy_to_full_disk_fails_gracefully(self):
        """Handle disk full error"""

    def test_copy_locked_file_retries(self):
        """Retry when file is locked"""

    def test_network_interruption_resume(self):
        """Resume after network failure"""

    def test_source_deleted_during_copy(self):
        """Handle source file deletion"""

class TestConflictResolution:
    """All conflict resolution strategies"""

    def test_skip_strategy_leaves_original(self):
        """Skip keeps original file"""

    def test_overwrite_strategy_replaces(self):
        """Overwrite replaces file"""

    def test_rename_strategy_creates_new(self):
        """Rename creates new file"""

    def test_prompt_strategy_user_decision(self):
        """User prompt for decision"""

class TestVerification:
    """File integrity verification"""

    def test_verify_checksum_after_copy(self):
        """Verify file integrity"""

    def test_verify_metadata_preserved(self):
        """Timestamps preserved"""

    def test_verify_permissions_preserved(self):
        """File permissions preserved"""
```

**Acceptance Criteria**:
- 15 tests passing
- Large file tests (1GB+)
- All error scenarios covered
- All conflict strategies tested
- Verification tests passing

---

### Task 2.2: Search Edge Cases Suite - 10 hours

**Status**: MINIMAL
**Risk**: MEDIUM - User experience impact
**Priority**: P1

**Tests to Implement**:

```python
# tests/test_search_edge_cases.py

class TestSearchInputValidation:
    """Input validation and sanitization"""

    def test_empty_query_handled(self):
        """Empty query returns no results"""

    def test_special_characters_in_query(self):
        """Handle ^$*.[]{}()?"\|+ chars"""

    def test_very_long_query_1000_chars(self):
        """Handle very long queries"""

    def test_null_bytes_in_query(self):
        """Reject null bytes"""

    def test_sql_injection_attempt_blocked(self):
        """Block SQL injection attempts"""

class TestSearchPaths:
    """Path handling edge cases"""

    def test_unicode_filenames(self):
        """Search Chinese/Arabic/Emoji names"""

    def test_paths_longer_than_max_path(self):
        """Handle paths > 260 chars"""

    def test_unc_network_paths(self):
        """Search UNC paths"""

    def test_nonexistent_directory(self):
        """Handle missing directories"""

    def test_symbolic_links(self):
        """Follow/ignore symlinks"""

class TestSearchPatterns:
    """Pattern matching edge cases"""

    def test_invalid_regex_pattern(self):
        """Handle invalid regex gracefully"""

    def test_wildcard_combinations(self):
        """Multiple wildcards (*.*.*)"""

    def test_case_sensitivity(self):
        """Case-sensitive vs insensitive"""

class TestSearchPerformance:
    """Performance under stress"""

    def test_search_with_100k_results(self):
        """Handle 100k+ results"""

    def test_search_timeout_after_30s(self):
        """Timeout long searches"""
```

**Acceptance Criteria**:
- 18 tests passing
- All input validation covered
- Path edge cases tested
- Pattern matching robust
- Performance acceptable

---

### Task 2.3: Integration Workflows - 8 hours

**Status**: INCOMPLETE
**Risk**: MEDIUM - End-to-end functionality
**Priority**: P1

**Tests to Implement**:

```python
# tests/test_integration_workflows.py

class TestSearchToOperationsWorkflow:
    """Complete search → operations flow"""

    def test_search_and_copy_files(self):
        """Search results → Copy operation"""

    def test_search_and_move_files(self):
        """Search results → Move operation"""

    def test_search_and_delete_files(self):
        """Search results → Delete with confirmation"""

class TestSearchToVaultWorkflow:
    """Search → encryption flow"""

    def test_search_and_encrypt_files(self):
        """Search results → Encrypt to vault"""

    def test_vault_search_encrypted_files(self):
        """Search within vault"""

class TestDuplicateWorkflow:
    """Complete duplicate detection flow"""

    def test_scan_review_delete_workflow(self):
        """Scan → Review → Delete duplicates"""

    def test_duplicate_scan_with_filters(self):
        """Filter duplicates by size/date"""

class TestExportWorkflow:
    """Export search results"""

    def test_export_to_csv_complete(self):
        """Full CSV export workflow"""

    def test_export_to_json_complete(self):
        """Full JSON export workflow"""
```

**Acceptance Criteria**:
- 10 tests passing
- End-to-end workflows tested
- Error propagation verified
- User experience validated

---

## Phase 3: MEDIUM PRIORITY (Week 2)

### Task 3.1: Performance Benchmark Suite - 8 hours

**Tests to Add**:
- Load testing (1M+ files)
- Stress testing (100 concurrent operations)
- Memory profiling
- Scalability benchmarks

### Task 3.2: Compatibility Testing - 6 hours

**Tests to Add**:
- Windows 10/11 matrix
- Python 3.10/3.11/3.12/3.13
- Different file systems (NTFS, FAT32, exFAT)
- Network drive scenarios

---

## Summary of Critical Tests Needed

| Priority | Category | Tests Needed | Time Estimate |
|----------|----------|--------------|---------------|
| P0 | Vault Security | 15 tests | 16 hours |
| P0 | Everything SDK | 12 tests | 12 hours |
| P0 | Fix Failing Tests | 8 fixes | 4 hours |
| P1 | Operations Reliability | 15 tests | 12 hours |
| P1 | Search Edge Cases | 18 tests | 10 hours |
| P1 | Integration Workflows | 10 tests | 8 hours |
| P2 | Performance Benchmarks | 10 tests | 8 hours |
| P2 | Compatibility | 12 tests | 6 hours |
| **TOTAL** | **8 categories** | **100 tests** | **76 hours** |

---

## Execution Plan

### Week 1 (Priority 0 - Blockers)
- **Monday**: Vault Security Suite (8 hours)
- **Tuesday**: Vault Security Suite (8 hours)
- **Wednesday**: Everything SDK Integration (8 hours)
- **Thursday**: Everything SDK Integration (4 hours) + Fix Failing Tests (4 hours)
- **Friday**: Code review + documentation

**Deliverable**: Vault tested, Everything SDK tested, all tests passing

### Week 2 (Priority 1 - High Priority)
- **Monday**: Operations Reliability (8 hours)
- **Tuesday**: Operations Reliability (4 hours) + Search Edge Cases (4 hours)
- **Wednesday**: Search Edge Cases (6 hours) + Integration Workflows (2 hours)
- **Thursday**: Integration Workflows (6 hours) + Buffer (2 hours)
- **Friday**: Full test suite run + documentation

**Deliverable**: 85%+ coverage, all critical paths tested

### Week 3 (Optional - Priority 2)
- **Monday-Wednesday**: Performance + Compatibility tests
- **Thursday-Friday**: Documentation + final review

---

## Success Metrics

### Coverage Targets
- **Vault**: 0% → 95% (CRITICAL)
- **Search**: 40% → 85%
- **Operations**: 55% → 90%
- **Integration**: 40% → 80%
- **Overall**: 65% → 85%

### Quality Targets
- All tests passing: 100%
- No import errors: 0
- No API mismatches: 0
- Performance benchmarks: Met
- Documentation: Complete

### Production Readiness
- **Before**: 60/100 (NOT READY)
- **After**: 85/100 (READY FOR BETA)

---

## Risk Mitigation

### If Vault Tests Take Longer
- Deprioritize steganography and anti-forensics
- Focus on core encryption/decryption
- Add remaining tests in Week 3

### If Everything SDK Not Available
- Use mocked tests for CI/CD
- Document manual testing procedure
- Add integration tests for when SDK is available

### If Time Runs Short
- Complete P0 tasks fully
- Partial P1 implementation
- Document remaining P2 tests for future

---

## Deliverables

1. **Test Files**:
   - `tests/test_vault_security.py` (NEW)
   - `tests/test_everything_integration.py` (NEW)
   - `tests/test_operations_reliability.py` (NEW)
   - `tests/test_search_edge_cases.py` (NEW)
   - `tests/test_integration_workflows.py` (NEW)
   - Updated existing test files

2. **Documentation**:
   - Test coverage report
   - Security testing guide
   - Performance benchmarks
   - Integration test documentation

3. **CI/CD**:
   - Updated GitHub Actions workflow
   - Test matrix for different environments
   - Coverage reporting integration

---

**Timeline**: 2 weeks
**Effort**: 76 hours
**Priority**: URGENT
**Status**: Ready to execute
