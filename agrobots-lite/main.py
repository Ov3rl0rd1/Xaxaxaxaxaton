import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agrolite.ui.gui import run_gui

if __name__ == "__main__":
    run_gui()
