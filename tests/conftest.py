"""Shared pytest configuration and fixtures."""

from pathlib import Path
import sys

# Ensure the project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
