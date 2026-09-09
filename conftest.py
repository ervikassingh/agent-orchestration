"""Root conftest for pytest — enables importlib mode to avoid package name collisions."""

import sys
from pathlib import Path

# Add each package's source directory to sys.path so tests can import
# the package modules directly (e.g., `from core_agent.settings import ...`).
ROOT = Path(__file__).parent
for pkg_dir in (ROOT / "packages").iterdir():
    if pkg_dir.is_dir() and (pkg_dir / "pyproject.toml").exists():
        src = pkg_dir / pkg_dir.name.replace("-", "_")
        if src.exists() and str(src) not in sys.path:
            sys.path.insert(0, str(src))
