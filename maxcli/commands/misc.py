"""Miscellaneous commands like backup and deploy."""

import os
import sys
import importlib.util
from pathlib import Path
from typing import Any, Callable, Optional
import shutil


def backup_db(_args):
    """Backup PostgreSQL database to timestamped file."""
    print("Backing up database... (this is a dummy command)")
    print("💡 This command needs to be implemented with your specific database backup logic.")
    print("Example: pg_dump mydb > ~/backups/db_$(date +%Y-%m-%d).sql")


def deploy_app(_args):
    """Deploy the application."""
    print("Deploying app... (this is a dummy command)")
    print("💡 This command needs to be implemented with your specific deployment logic.")
    print("Typical steps might include:")
    print("  - Building the application")
    print("  - Running tests")
    print("  - Pushing to container registry")
    print("  - Updating Kubernetes deployments")
    print("  - Running post-deployment checks")


def _check_pandas_availability() -> bool:
    """Check if pandas is available and provide helpful error message if not.
    
    Returns:
        True if pandas is available, False otherwise.
    """
    try:
        import pandas  # noqa: F401
        return True
    except ImportError:
        print("❌ Error: pandas is required for CSV processing functionality.")
        print("💡 Please install pandas using one of the following commands:")
        print("   pip install pandas")
        print("   conda install pandas")
        print("   poetry add pandas")
        return False


def _get_saved_functions_dir() -> Path:
    """Get the directory path for saved function files.
    
    Returns:
        Path object pointing to the saved functions directory.
    """
    maxcli_dir = Path(__file__).parent.parent
    saved_functions_dir = maxcli_dir / "saved_functions"
    saved_functions_dir.mkdir(exist_ok=True)
    return saved_functions_dir


def _validate_csv_file(csv_path: str) -> bool:
    """Validate that the CSV file exists and is readable.
    
    Args:
        csv_path: Path to the CSV file.
        
    Returns:
        True if file is valid, False otherwise.
    """
    try:
        if not os.path.exists(csv_path):
            print(f"❌ Error: CSV file not found: {csv_path}")
            return False
        
        # Try to read the first few rows to validate CSV format
        # Import pandas here since we've already checked availability
        import pandas as pd
        pd.read_csv(csv_path, nrows=1)
        return True
    except Exception as e:
        print(f"❌ Error: Invalid CSV file: {e}")
        return False


def _validate_python_file(python_path: str) -> bool:
    """Validate that the Python file exists and is readable.
    
    Args:
        python_path: Path to the Python file.
        
    Returns:
        True if file is valid, False otherwise.
    """
    try:
        if not os.path.exists(python_path):
            print(f"❌ Error: Python file not found: {python_path}")
            return False
        
        if not python_path.endswith('.py'):
            print(f"❌ Error: File must have .py extension: {python_path}")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error: Invalid Python file: {e}")
        return False


def _load_function_from_file(python_path: str) -> Optional[Callable[..., Any]]:
    """Load and return the main processing function from a Python file.
    
    The Python file should contain a function named 'process_data' that takes
    a pandas DataFrame as input and returns the processed result.
    
    Args:
        python_path: Path to the Python file containing the function.
        
    Returns:
        The process_data function if found, None otherwise.
    """
    try:
        spec = importlib.util.spec_from_file_location("user_function", python_path)
        if spec is None or spec.loader is None:
            print(f"❌ Error: Could not load module from {python_path}")
            return None
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if not hasattr(module, 'process_data'):
            print("❌ Error: Python file must contain a 'process_data' function")
            print("💡 Example function signature: def process_data(df: pd.DataFrame) -> Any:")
            return None
            
        func = getattr(module, 'process_data')
        return func if callable(func) else None
    except Exception as e:
        print(f"❌ Error loading function from file: {e}")
        return None


def _save_function_file(source_path: str, save_name: str) -> bool:
    """Save a function file to the saved functions directory.
    
    Args:
        source_path: Path to the source Python file.
        save_name: Name to save the file as (without .py extension).
        
    Returns:
        True if saved successfully, False otherwise.
    """
    try:
        saved_functions_dir = _get_saved_functions_dir()
        destination_path = saved_functions_dir / f"{save_name}.py"
        
        shutil.copy2(source_path, destination_path)
        print(f"✅ Function saved as: {destination_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving function: {e}")
        return False


def _list_saved_functions() -> None:
    """List all saved function files."""
    saved_functions_dir = _get_saved_functions_dir()
    py_files = list(saved_functions_dir.glob("*.py"))
    
    if not py_files:
        print("📁 No saved functions found.")
        return
        
    print("📁 Saved functions:")
    for py_file in sorted(py_files):
        print(f"  • {py_file.stem}")


def process_csv_data(args) -> None:
    """Process CSV data using a Python function file.
    
    This command takes a CSV file and a Python function file, loads the CSV data
    into a pandas DataFrame, and applies the function from the Python file to process it.
    
    The Python file should contain a function named 'process_data' that accepts
    a pandas DataFrame as input and returns the processed result.
    
    Args:
        args: Command line arguments containing csv_file, function_file, and optional flags.
    """
    # Check pandas availability first
    if not _check_pandas_availability():
        return
        
    # Import pandas here after checking availability
    import pandas as pd
    
    # Handle listing saved functions
    if args.list_saved:
        _list_saved_functions()
        return
        
    # Validate required arguments
    if not args.csv_file or not args.function_file:
        print("❌ Error: Both --csv-file and --function-file are required")
        return
        
    # Validate input files
    if not _validate_csv_file(args.csv_file):
        return
        
    if not _validate_python_file(args.function_file):
        return
        
    try:
        # Load CSV data
        print(f"📊 Loading CSV data from: {args.csv_file}")
        df = pd.read_csv(args.csv_file)
        print(f"✅ Loaded {len(df)} rows and {len(df.columns)} columns")
        
        # Load and execute function
        print(f"🐍 Loading function from: {args.function_file}")
        process_function = _load_function_from_file(args.function_file)
        
        if process_function is None:
            return
            
        print("🚀 Processing data...")
        result = process_function(df)
        
        # Display result
        print("✅ Processing completed!")
        print("\n📋 Result:")
        print("=" * 50)
        
        if hasattr(result, 'to_string'):
            # If result is a DataFrame or Series
            print(result.to_string())
        else:
            # For other types of results
            print(result)
            
        print("=" * 50)
        
        # Save function if requested
        if args.save_as:
            if _save_function_file(args.function_file, args.save_as):
                print(f"💾 Function saved for future use with name: {args.save_as}")
                
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        sys.exit(1) 