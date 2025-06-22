import sys
import os

# Add the main directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui_app import main

if __name__ == "__main__":
    main()
