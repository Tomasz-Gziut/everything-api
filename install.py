#!/usr/bin/env python3
"""Install requirements for main app and all submodules, isolating conflicts with venvs."""
import configparser
import subprocess
import sys
import venv
from pathlib import Path

BASE_DIR = Path(__file__).parent


def run(cmd, **kwargs):
    subprocess.run(cmd, check=True, **kwargs)


# Install main requirements into the current environment
run([sys.executable, "-m", "pip", "install", "-r", str(BASE_DIR / "requirements.txt")])

# Install each submodule's requirements into its own venv
config = configparser.ConfigParser()
config.read(BASE_DIR / ".gitmodules")

for section in config.sections():
    if "path" not in config[section]:
        continue
    subdir = BASE_DIR / config[section]["path"]
    req = subdir / "requirements.txt"
    if not req.exists():
        continue

    venv_dir = subdir / ".venv"
    print(f"[install] Creating venv for {subdir.name} ...")
    venv.create(str(venv_dir), with_pip=True, clear=True)

    venv_python = venv_dir / "bin" / "python"
    print(f"[install] Installing {req}")
    run([str(venv_python), "-m", "pip", "install", "-r", str(req)])
