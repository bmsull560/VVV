import sys
import os

# Add the project root directory to sys.path
# This allows pytest to find modules like 'agents' and 'src'
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
