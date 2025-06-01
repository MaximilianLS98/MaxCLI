"""
CLI test runner for MaxCLI testing.

Provides utilities to run tests efficiently and generate reports.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def run_test_suite(
    test_path: Optional[str] = None,
    verbose: bool = False,
    coverage: bool = True,
    parallel: bool = True
) -> int:
    """Run the complete test suite with configurable options.
    
    Args:
        test_path: Specific test path to run (None for all tests).
        verbose: Enable verbose output.
        coverage: Enable coverage reporting.
        parallel: Enable parallel test execution.
        
    Returns:
        Exit code from pytest.
    """
    cmd = ["python", "-m", "pytest"]
    
    if test_path:
        cmd.append(test_path)
    else:
        cmd.append("tests/")
    
    if verbose:
        cmd.extend(["-v", "-s"])
    
    if coverage:
        cmd.extend([
            "--cov=maxcli",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "--cov-fail-under=0"  # Don't fail on low coverage in CI
        ])
    
    if parallel:
        cmd.extend(["-n", "auto"])  # Requires pytest-xdist
    
    # Add other useful flags
    cmd.extend([
        "--tb=short",  # Shorter tracebacks
        "--strict-markers",  # Require marker registration
    ])
    
    return subprocess.run(cmd).returncode


def run_specific_module_tests(module_name: str) -> int:
    """Run tests for a specific module.
    
    Args:
        module_name: Name of the module to test.
        
    Returns:
        Exit code from pytest.
    """
    test_file = f"tests/unit/test_{module_name}.py"
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return 1
    
    return run_test_suite(test_path=test_file, verbose=True)


def run_integration_tests() -> int:
    """Run integration tests only.
    
    Returns:
        Exit code from pytest.
    """
    return run_test_suite(test_path="tests/integration/", verbose=True)


def run_unit_tests() -> int:
    """Run unit tests only.
    
    Returns:
        Exit code from pytest.
    """
    return run_test_suite(test_path="tests/unit/", verbose=True)


def run_quick_tests() -> int:
    """Run tests without coverage for quick feedback.
    
    Returns:
        Exit code from pytest.
    """
    return run_test_suite(coverage=False, parallel=True)


def run_coverage_report() -> int:
    """Generate coverage report only.
    
    Returns:
        Exit code from coverage command.
    """
    cmd = ["python", "-m", "coverage", "html"]
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("📊 Coverage report generated in htmlcov/index.html")
    
    return result.returncode


def run_linting() -> int:
    """Run code linting on the project.
    
    Returns:
        Exit code from linting tools.
    """
    print("🔍 Running code linting...")
    
    # Run flake8
    flake8_result = subprocess.run([
        "python", "-m", "flake8", "maxcli/", "tests/", "--max-line-length=120"
    ])
    
    # Run mypy  
    mypy_result = subprocess.run([
        "python", "-m", "mypy", "maxcli/", "--ignore-missing-imports"
    ])
    
    if flake8_result.returncode == 0 and mypy_result.returncode == 0:
        print("✅ Linting passed!")
        return 0
    else:
        print("❌ Linting failed!")
        return 1


def run_all_checks() -> int:
    """Run all quality checks: tests and linting.
    
    Returns:
        Exit code (0 if all pass, 1 if any fail).
    """
    print("🚀 Running all quality checks...")
    
    checks = [
        ("📋 Running tests", lambda: run_test_suite()),
        ("🔍 Running linting", run_linting),
    ]
    
    failed_checks = []
    
    for check_name, check_func in checks:
        print(f"\n{check_name}...")
        result = check_func()
        
        if result != 0:
            failed_checks.append(check_name)
    
    print(f"\n{'='*50}")
    print("📊 Quality Check Results")
    print(f"{'='*50}")
    
    if not failed_checks:
        print("✅ All checks passed!")
        return 0
    else:
        print(f"❌ {len(failed_checks)} check(s) failed:")
        for check in failed_checks:
            print(f"  • {check}")
        return 1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run MaxCLI tests")
    parser.add_argument("--module", help="Test specific module")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--quick", action="store_true", help="Run quick tests (no coverage)")
    parser.add_argument("--coverage-only", action="store_true", help="Generate coverage report only")
    parser.add_argument("--lint", action="store_true", help="Run linting only")
    parser.add_argument("--all", action="store_true", help="Run all quality checks")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage")
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel execution")
    parser.add_argument("path", nargs="?", help="Specific test path")
    
    args = parser.parse_args()
    
    # Handle specific actions
    if args.all:
        exit_code = run_all_checks()
    elif args.coverage_only:
        exit_code = run_coverage_report()
    elif args.lint:
        exit_code = run_linting()
    elif args.module:
        exit_code = run_specific_module_tests(args.module)
    elif args.integration:
        exit_code = run_integration_tests()
    elif args.unit:
        exit_code = run_unit_tests()
    elif args.quick:
        exit_code = run_quick_tests()
    else:
        # Default: run test suite with options
        exit_code = run_test_suite(
            test_path=args.path,
            verbose=args.verbose,
            coverage=not args.no_coverage,
            parallel=not args.no_parallel
        )
    
    sys.exit(exit_code) 