"""Root pytest configuration for the src-layout packages."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent
for package_name in ("orchestrator", "api-server", "rag-pipeline", "tool-library"):
    package_dir = ROOT / "packages" / package_name / "src"
    if str(package_dir) not in sys.path:
        sys.path.insert(0, str(package_dir))
