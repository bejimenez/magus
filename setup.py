"""Setup script for the Name Generator API MVP package.
This script helps set up the development environment
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command: str, description: str) -> bool:
    """Run a shell command and return success status."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with error:\n{e.stderr.strip()}")
        return False
    
def check_python_version():
    """Check if the Python version is 3.8 or higher."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("Python 3.8 or higher is required.")
        return False
    print(f"✓ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def setup_virtual_environment():
    """Create and activate virtual environment."""
    venv_path = Path("venv")

    if venv_path.exists():
        print("Virtual environment already exists. Skipping creation.")
        return True
    
    # Create virtual environment
    if not run_command(f"{sys.executable} -m venv venv", "Creating virtual environment"):
        return False
    
    print("✓ Virtual environment created")
    print("  To activate manually:")
    if os.name == 'nt':  # Windows
        print("    venv\\Scripts\\activate")
    else:  # Unix/Linux/Mac
        print("    source venv/bin/activate")
    
    return True

def install_dependencies():
    """Install required dependencies from requirements.txt."""
    if os.name == 'nt': #windows
        pip_path = "venv\\Scripts\\pip"
    else:  # Unix/Linux/Mac
        pip_path = "venv/bin/pip"

    # Install requirements
    return run_command(f"{pip_path} install -r requirements.txt", "Installing dependencies")

def create_run_script():
    """Create a convenient run script"""
    if os.name == 'nt':  # Windows
        script_content = """@echo off
echo Starting Name Generator API...
venv\\Scripts\\python main.py
"""
        script_name = "run.bat"
    else:  # Unix/Linux/Mac
        script_content = """#!/bin/bash
echo "Starting Name Generator API..."
source venv/bin/activate
python main.py
"""
        script_name = "run.sh"
    
    with open(script_name, 'w') as f:
        f.write(script_content)
    
    if os.name != 'nt':
        os.chmod(script_name, 0o755)  # Make executable on Unix systems
    
    print(f"✓ Created {script_name} for easy startup")
    return True

def main():
    """Main setup function"""
    print("Name Generator API MVP Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Setup virtual environment
    if not setup_virtual_environment():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Create run script
    create_run_script()
    
    print("\n" + "=" * 40)
    print("✓ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Run the API server:")
    if os.name == 'nt':
        print("   run.bat")
    else:
        print("   ./run.sh")
    print("   OR manually:")
    if os.name == 'nt':
        print("   venv\\Scripts\\python main.py")
    else:
        print("   source venv/bin/activate && python main.py")
    print("\n2. Test the API (in another terminal):")
    if os.name == 'nt':
        print("   venv\\Scripts\\python test_api.py")
    else:
        print("   source venv/bin/activate && python test_api.py")
    print("\n3. Visit http://localhost:8000/docs for interactive API documentation")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)