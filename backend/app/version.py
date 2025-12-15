"""Version utilities for reading version from pyproject.toml"""

import re
from pathlib import Path


def get_version() -> str:
    """Read version from pyproject.toml"""
    try:
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "r") as f:
            content = f.read()
        # Match version = "x.y.z" pattern
        match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
        if match:
            return match.group(1)
        return "unknown"
    except Exception:
        return "unknown"
