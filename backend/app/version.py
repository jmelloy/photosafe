"""Version utilities for reading version from pyproject.toml"""

import os
import re
import subprocess
from pathlib import Path


def get_git_sha() -> str:
    """Get the current git SHA"""
    try:
        # Try environment variable first (set during Docker build)
        sha = os.environ.get("GIT_SHA")
        if sha:
            return sha
        
        # Fall back to git command
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return "unknown"
    except Exception:
        return "unknown"


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


def get_version_info() -> dict:
    """Get complete version information including git SHA"""
    return {
        "version": get_version(),
        "git_sha": get_git_sha()
    }
