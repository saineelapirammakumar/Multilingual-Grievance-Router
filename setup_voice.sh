#!/usr/bin/env bash
set -euo pipefail

# Run from the project root with the project's Python 3.12 virtualenv activated.
if [[ ! -f "backend.py" || ! -f "scripts/download_model.py" ]]; then
  echo "Run this script from the multilingual_grievance_router project root." >&2
  exit 2
fi
python - <<'PY'
import sys
if sys.version_info[:2] != (3, 12):
    raise SystemExit(f"Use Python 3.12 for the tested environment (found {sys.version.split()[0]}).")
PY

python -m pip install "faster-whisper==1.2.1" "huggingface-hub==0.36.2" "av==16.1.0"
python scripts/download_model.py asr --output "$PWD/local_models/asr"

python - <<'PY'
from pathlib import Path
root = Path.cwd()
env = root / '.env'
model = str((root / 'local_models' / 'asr').resolve())
lines = env.read_text().splitlines() if env.exists() else []
updated = False
for i, line in enumerate(lines):
    if line.strip().startswith('ASR_MODEL_PATH='):
        lines[i] = f'ASR_MODEL_PATH={model}'
        updated = True
        break
if not updated:
    lines.append(f'ASR_MODEL_PATH={model}')
env.write_text('\n'.join(lines).rstrip() + '\n')
print(f'Updated ASR_MODEL_PATH in {env} to {model}')
print('Restart FastAPI after this script completes.')
PY
