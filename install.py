#!/usr/bin/env python3
"""Install requirements for main app and all submodules automatically."""
import configparser
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent


def run(cmd):
    subprocess.run(cmd, check=True)


run([sys.executable, "-m", "pip", "install", "-r", str(BASE_DIR / "requirements.txt")])

config = configparser.ConfigParser()
config.read(BASE_DIR / ".gitmodules")

for section in config.sections():
    if "path" not in config[section]:
        continue
    req = BASE_DIR / config[section]["path"] / "requirements.txt"
    if req.exists():
        print(f"[install] {req}")
        run([sys.executable, "-m", "pip", "install", "-r", str(req)])
