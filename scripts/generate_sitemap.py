#!/usr/bin/env python3
"""
Wrapper: calls the main generate_sitemap.py from repo root.
Kept here so existing scripts that call scripts/generate_sitemap.py still work.
"""
import subprocess
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
script = repo_root / 'generate_sitemap.py'

result = subprocess.run([sys.executable, str(script)], cwd=str(repo_root))
sys.exit(result.returncode)
