import os
import sys


# Add ../langlang to the path so tests can find all the things.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'langlang')))