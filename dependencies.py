import subprocess
import sys

# List of required packages
required_packages = [
    'PySide6',
    'numpy',
    'pandas',
    'matplotlib',
    'networkx',
    'itertools',  # Part of standard library, no need to install separately
    'suda2',
    'piflib',
    'seaborn'
]

def install(package):
    """Install the given package using pip."""
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def main():
    """Install all required packages."""
    for package in required_packages:
        try:
            print(f"Installing {package}...")
            install(package)
            print(f"{package} installed successfully!")
        except subprocess.CalledProcessError:
            print(f"Failed to install {package}. Please try manually.")
            
if __name__ == "__main__":
    main()
