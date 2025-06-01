# MaxCLI Testing Framework

This directory contains comprehensive testing for the MaxCLI modular command-line interface system. The testing framework is designed to ensure reliability, maintainability, and quality across all modules.

## 📁 Directory Structure

```
tests/
├── README.md                     # This file
├── conftest.py                   # Shared pytest fixtures
├── fixtures/                     # Test data and mock configurations
│   ├── modules/                  # Sample module configurations
│   └── test_data/               # Test datasets
├── integration/                  # Integration tests
│   └── test_cli_integration.py  # CLI command registration and module loading
├── unit/                        # Unit tests
│   ├── test_module_manager.py   # Module management functionality
│   └── test_docker_manager.py   # Docker management functionality
└── utils/                       # Testing utilities
    ├── test_helpers.py          # Common test helper functions
    └── cli_test_runner.py       # Test execution utilities
```

## 🚀 Quick Start

### Running All Tests

```bash
# Run all tests with coverage
python tests/utils/cli_test_runner.py

# Run with verbose output
python tests/utils/cli_test_runner.py --verbose

# Run quick tests (no coverage)
python tests/utils/cli_test_runner.py --quick
```

### Running Specific Test Types

```bash
# Unit tests only
python tests/utils/cli_test_runner.py --unit

# Integration tests only (no coverage)
python tests/utils/cli_test_runner.py --integration

# Integration tests with coverage (5% threshold)
python tests/utils/cli_test_runner.py --integration-cov

# Specific module tests
python tests/utils/cli_test_runner.py --module docker_manager
```

### Development Workflow

```bash
# Run all quality checks (tests + linting + formatting)
python tests/utils/cli_test_runner.py --all

# Quick feedback during development
python tests/utils/cli_test_runner.py --quick

# Generate coverage report
python tests/utils/cli_test_runner.py --coverage-only
```

## 🔧 Test Categories

### Unit Tests (`tests/unit/`)

Unit tests focus on individual components in isolation:

- **Module Manager Tests**: Test module discovery, loading, validation, and error handling
- **Docker Manager Tests**: Test Docker operations, container management, and error scenarios
- **Core Functionality Tests**: Test CLI parsing, configuration management, and utilities

### Integration Tests (`tests/integration/`)

Integration tests verify component interactions:

- **CLI Integration**: Test command registration and module loading
- **Module Combinations**: Test various module combinations and dependencies
- **End-to-End Workflows**: Test complete user workflows

### Fixtures and Test Data (`tests/fixtures/`)

Reusable test data and configurations:

- **Module Configurations**: Sample module.json files for testing
- **Mock Data**: Standardized test datasets
- **Environment Setups**: Pre-configured test environments

## 🛠 Test Utilities

### Shared Fixtures (`tests/conftest.py`)

Common pytest fixtures available to all tests:

- `mock_module_manager`: Configured ModuleManager instance
- `sample_modules`: Collection of test module configurations
- `temp_config_dir`: Temporary directory for configuration files
- `docker_available`: Conditional fixture for Docker availability

### Test Helpers (`tests/utils/test_helpers.py`)

Utility functions for testing:

- `mock_subprocess_run()`: Mock subprocess calls
- `capture_cli_output()`: Capture CLI command output
- `create_temp_module()`: Create temporary module configurations
- `validate_module_config()`: Validate module configuration structure

### Test Runner (`tests/utils/cli_test_runner.py`)

Comprehensive test execution utility:

- **Flexible Execution**: Run specific tests, modules, or complete suites
- **Coverage Reporting**: Generate HTML and terminal coverage reports
- **Quality Checks**: Integrate linting and formatting checks
- **Parallel Execution**: Utilize multiple cores for faster testing

## 📋 Testing Best Practices

### 1. Test Organization

```python
class TestModuleManager:
    """Group related tests in classes for better organization."""

    def test_discover_modules_success(self):
        """Test successful module discovery."""
        pass

    def test_discover_modules_invalid_config(self):
        """Test handling of invalid module configurations."""
        pass
```

### 2. Functional Testing Style

Following the user's preference for functional programming:

```python
def test_module_loading_functional():
    """Use functional testing approaches where possible."""
    # Arrange
    modules = create_test_modules()

    # Act
    result = load_modules_functionally(modules)

    # Assert
    assert_valid_loading_result(result)
```

### 3. Descriptive Test Names

```python
def test_docker_manager_handles_missing_docker_gracefully():
    """Test names should clearly describe what is being tested."""
    pass

def test_module_manager_validates_config_schema_strictly():
    """Include expected behavior in the test name."""
    pass
```

### 4. Comprehensive Assertions

```python
def test_module_registration():
    """Use multiple assertions to validate complete behavior."""
    result = register_module("test_module")

    assert result.success is True
    assert result.module_name == "test_module"
    assert result.commands_registered > 0
    assert result.errors == []
```

### 5. Mock External Dependencies

```python
@patch('subprocess.run')
def test_docker_command_execution(mock_run):
    """Mock external commands for predictable testing."""
    mock_run.return_value = MagicMock(returncode=0, stdout="success")

    result = execute_docker_command("ps")

    assert result.success is True
    mock_run.assert_called_once()
```

## 🔍 Debugging Tests

### Running with Debug Output

```bash
# Verbose output with print statements
pytest tests/ -v -s

# Show local variables on failure
pytest tests/ --tb=long

# Drop into debugger on failure
pytest tests/ --pdb
```

### Test Coverage Analysis

```bash
# Generate detailed coverage report
coverage run -m pytest tests/
coverage report --show-missing
coverage html  # Open htmlcov/index.html
```

### Performance Profiling

```bash
# Profile test execution time
pytest tests/ --durations=10

# Memory usage analysis
pytest tests/ --memray
```

## 🔄 Continuous Integration

### GitHub Actions Integration

The `.github/workflows/test-modules.yml` workflow provides:

- **Multi-Platform Testing**: Ubuntu, macOS, and Windows
- **Python Version Matrix**: Python 3.8-3.12
- **Quality Checks**: Linting, formatting, and type checking
- **Security Scanning**: Dependency and code security analysis
- **Performance Testing**: Memory usage and execution time monitoring

### Local Pre-commit Hooks

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## 📊 Coverage Goals

- **Minimum Coverage**: 80% overall code coverage
- **Critical Paths**: 95% coverage for core functionality
- **Error Handling**: 100% coverage for error scenarios
- **Public APIs**: 100% coverage for all public methods

## 🐛 Common Issues and Solutions

### Docker Tests Failing

```bash
# Ensure Docker is running
sudo systemctl start docker

# Run Docker tests in isolation
pytest tests/unit/test_docker_manager.py -v
```

### Import Errors

```bash
# Install package in development mode
pip install -e .

# Verify Python path
python -c "import maxcli; print(maxcli.__file__)"
```

### Slow Test Execution

```bash
# Use parallel execution
pytest tests/ -n auto

# Run only fast tests
pytest tests/ -m "not slow"
```

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Plugin](https://pytest-cov.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Test-Driven Development Guide](https://testdriven.io/)

## 🤝 Contributing to Tests

When adding new functionality to MaxCLI:

1. **Write Tests First**: Follow TDD principles
2. **Maintain Coverage**: Ensure new code has appropriate test coverage
3. **Update Documentation**: Keep this README and docstrings current
4. **Run All Checks**: Use `--all` flag before submitting changes

```bash
# Complete pre-submission check
python tests/utils/cli_test_runner.py --all
```

---

For questions about the testing framework, please refer to the module documentation or create an issue in the project repository.

## 🏗 CI/CD Integration

### GitHub Actions / CI Environments

For continuous integration, use different commands based on test type:

```bash
# Unit tests with full coverage requirements (20%)
python -m pytest tests/unit/ -v --cov=maxcli --cov-report=xml --cov-report=term-missing

# Integration tests without coverage (recommended for CI)
python -m pytest tests/integration/ -v --no-cov

# Integration tests with coverage (5% threshold)
python -m pytest tests/integration/ -v --cov=maxcli --cov-report=xml --cov-report=term-missing --cov-fail-under=5

# All tests with appropriate coverage thresholds
python tests/utils/cli_test_runner.py --all
```

### Coverage Requirements by Test Type

- **Unit Tests**: 20% minimum coverage (tests individual components)
- **Integration Tests**: 5% minimum coverage (tests workflows, naturally lower coverage)
- **Combined Test Suite**: 20% minimum coverage (balanced approach)

### Troubleshooting CI Test Failures

1. **Import Errors**: Ensure all test directories have `__init__.py` files
2. **AsyncIO Warnings**: Configuration is handled in `pyproject.toml`
3. **Coverage Failures**: Use appropriate coverage thresholds for test type
4. **Module Not Found**: Check Python path and module structure

```bash
# Debug import issues
python -c "import tests.utils.test_helpers; print('Imports OK')"

# Verify pytest configuration
python -m pytest --collect-only
```
