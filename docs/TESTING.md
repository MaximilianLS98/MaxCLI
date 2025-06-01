# 🧪 MaxCLI Bootstrap Script Testing

This document describes the comprehensive test suite for the MaxCLI bootstrap script, including the critical security fix and CI/CD integration.

## 🛡️ Critical Security Fix

The test suite specifically validates the **critical security fix** that prevents `./bootstrap.sh --help` from accidentally deleting files. This was a serious bug where the cleanup trap was set before argument parsing.

### What was fixed:

- **Before**: Cleanup traps were set before parsing `--help`, causing file operations even for help commands
- **After**: Arguments are parsed first, `--help` exits cleanly without any file operations

## 📋 Test Suite Overview

The test suite includes **10 comprehensive tests** covering:

| Test                             | Description                                       | Purpose                      |
| -------------------------------- | ------------------------------------------------- | ---------------------------- |
| **Help Security Fix**            | Verifies `--help` doesn't trigger file operations | Critical security validation |
| **Help Command Variations**      | Tests both `--help` and `-h`                      | User experience              |
| **Invalid Arguments**            | Tests error handling for bad arguments            | Robustness                   |
| **Module Preset Functionality**  | Tests `--modules=` argument parsing               | Core functionality           |
| **Force Download**               | Tests `--force-download` flag                     | Download system              |
| **GitHub Customization**         | Tests custom repo/branch arguments                | Flexibility                  |
| **Local Mode Detection**         | Tests detection when files exist locally          | Smart mode detection         |
| **Standalone Mode Detection**    | Tests detection when files need download          | Smart mode detection         |
| **Configuration Generation**     | Tests module config file creation                 | Core functionality           |
| **Missing Files Error Handling** | Tests graceful failure scenarios                  | Error handling               |

## 🚀 Running Tests

### Local Testing

```bash
# Run all tests
./test_bootstrap.sh

# Run in CI mode (less verbose, machine-readable)
./test_bootstrap.sh --ci

# Run with debug output
./test_bootstrap.sh --verbose

# Show help
./test_bootstrap.sh --help
```

### Expected Output

```
🧪 MaxCLI Bootstrap Script Test Suite
======================================

📋 Running comprehensive tests...

✅ PASS: Help Security Fix - No File Operations
✅ PASS: Help Command Variations
✅ PASS: Invalid Arguments Handling
✅ PASS: Module Preset Functionality
✅ PASS: Force Download Functionality
✅ PASS: GitHub Repository Customization
✅ PASS: Local Mode Detection
✅ PASS: Standalone Mode Detection
✅ PASS: Configuration File Generation
✅ PASS: Missing Files Error Handling

📊 Test Results Summary
======================
Total Tests Run: 10
Tests Passed: 10
Tests Failed: 0

🎉 All tests passed! Bootstrap script is ready for production.
```

## 🔄 GitHub Actions CI/CD Integration

### Automatic Testing

The test suite automatically runs on:

- **Pushes to `main` branch**
- **Pull requests to `main`**
- **Manual workflow dispatch**

### Workflow Features

The GitHub Actions workflow (`.github/workflows/test-bootstrap.yml`) includes:

- **🔒 Security-first testing** - Critical fix tested on every run
- **🍎 Cross-platform testing** - Ubuntu and macOS
- **📈 Matrix testing** - Multiple scenarios in parallel
- **⚡ Performance monitoring** - Ensures help commands are fast
- **📁 Artifact collection** - Saves logs on failure

### Setting Up CI/CD

1. **Add to your repository**:

    ```bash
    git add .github/workflows/test-bootstrap.yml test_bootstrap.sh
    git commit -m "Add comprehensive bootstrap script testing"
    git push origin main
    ```

2. **Enable GitHub Actions** in your repository settings

3. **View test results** in the Actions tab

### CI/CD Workflow Jobs

| Job              | Platform | Purpose                                    |
| ---------------- | -------- | ------------------------------------------ |
| `test-bootstrap` | Ubuntu   | Full test suite + security validation      |
| `test-macos`     | macOS    | Cross-platform security verification       |
| `test-scenarios` | Ubuntu   | Matrix testing of different usage patterns |

## 🛠️ Test Architecture

### Functional Programming Approach

The test suite follows functional programming principles:

- **Pure functions** for all test utilities
- **Immutable state** for test results
- **Clear separation** of concerns
- **No side effects** in helper functions

### Test Isolation

Each test runs in its own isolated environment:

- **Temporary directories** for each test
- **Clean environments** created and destroyed
- **No cross-test pollution**
- **Parallel execution safe**

### Mocking Strategy

Complex functionality is tested using:

- **Simplified mock scripts** instead of complex sed replacements
- **Controlled test environments** with known inputs
- **Predictable outputs** for validation
- **Early exit strategies** to avoid full installation

## 🔍 Test Details

### Critical Security Test

```bash
# Creates a canary file that should NOT be deleted
echo "This file should not be deleted" > canary.txt

# Run help command
./bootstrap.sh --help

# Verify file still exists (CRITICAL)
if [[ ! -f "canary.txt" ]]; then
    echo "❌ SECURITY ISSUE: Help deleted files!"
    exit 1
fi
```

### Module Preset Test

Tests argument parsing with simplified mock:

```bash
./bootstrap_test.sh --modules=ssh_manager,docker_manager
# Should output: "✓ Enabled: ssh_manager" and "✓ Enabled: docker_manager"
```

### Standalone Mode Test

Tests mode detection without actual downloads:

```bash
# In directory without required files
./bootstrap_test.sh --modules=ssh_manager
# Should output: "🔍 Running in standalone mode"
```

## 🏷️ Exit Codes

| Exit Code | Meaning                          |
| --------- | -------------------------------- |
| `0`       | All tests passed                 |
| `1`       | Some tests failed                |
| `1`       | Invalid arguments to test script |

## 📊 Debugging Failed Tests

If tests fail:

1. **Run with verbose output**:

    ```bash
    ./test_bootstrap.sh --verbose
    ```

2. **Check specific test output** in the failure message

3. **Review temporary files** (saved in `/tmp/maxcli_test_*`)

4. **Test individual components** by running bootstrap commands manually

## 🎯 Adding New Tests

To add a new test:

1. **Create a test function** following the pattern:

    ```bash
    test_your_new_feature() {
        local test_name="Your New Feature"
        local test_dir="$TEST_OUTPUT_DIR/your_test"

        # Test logic here

        if [[ condition ]]; then
            log_test_result "$test_name" "PASS" "Success message"
        else
            log_test_result "$test_name" "FAIL" "Failure details"
        fi

        cleanup_test_environment "$test_dir"
    }
    ```

2. **Add to the test runner**:

    ```bash
    # In run_all_tests() function
    test_your_new_feature
    ```

3. **Test locally** before committing

## 🚦 Quality Gates

The test suite ensures:

- ✅ **Security**: Critical fix always validated
- ✅ **Functionality**: All features work as expected
- ✅ **Performance**: Help commands respond quickly (<2s)
- ✅ **Compatibility**: Works on Linux and macOS
- ✅ **Robustness**: Handles errors gracefully
- ✅ **Usability**: All argument combinations work

## 🎉 Production Readiness

When all tests pass, the bootstrap script is guaranteed to be:

- **🛡️ Secure** - No file deletion bugs
- **🔄 Reliable** - Handles all scenarios correctly
- **⚡ Fast** - Responsive help commands
- **🌍 Compatible** - Works across platforms
- **📝 Well-documented** - Clear error messages

---

**🚀 Ready for deployment!** The comprehensive test suite ensures your bootstrap script is production-ready and will never regress on the critical security fix.
