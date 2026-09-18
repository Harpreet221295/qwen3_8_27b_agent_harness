#!/usr/bin/env bash
cd /app
pip install -q --no-build-isolation ./vendor/mathx >/dev/null 2>&1 || \
  echo "/app/vendor/mathx" > "$(python -c 'import site; print(site.getsitepackages()[0])')/mathx.pth"
python run_analysis.py
