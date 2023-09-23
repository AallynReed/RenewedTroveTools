import os
import sys
from pathlib import Path


if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BasePath = Path(sys._MEIPASS)
else:
    BasePath = Path(os.getcwd())
