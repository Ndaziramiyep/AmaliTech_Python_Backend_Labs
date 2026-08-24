"""Convenience entry point so `python main.py <command> ...` runs the CLI without requiring `pip install -e .` first."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))

from social.cli.__main__ import main

if __name__ == "__main__":
    main()
