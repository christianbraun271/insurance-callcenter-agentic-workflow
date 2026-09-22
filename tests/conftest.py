import sys
from pathlib import Path

# Make the project root importable as `src.*` regardless of where pytest is
# invoked from, without needing a packaging/pyproject.toml setup for what is
# still a small, single-purpose demo.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
