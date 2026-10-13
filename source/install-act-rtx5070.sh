#!/usr/bin/env bash
# Install ACT extras without replacing the verified RoboTwin CUDA environment.
set -euo pipefail
ACT_OUTPUTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${ACT_OUTPUTS}/activate-robotwin.sh"
python - <<'PY'
import torch, torchvision
assert torch.__version__ == '2.7.1+cu128', torch.__version__
assert torchvision.__version__ == '0.22.1+cu128', torchvision.__version__
assert torch.cuda.is_available(), 'CUDA is unavailable'
PY
python -m pip install -c "${ACT_OUTPUTS}/act-preserve-constraints.txt" -r "${ACT_OUTPUTS}/act-extra-requirements.txt"
python -m pip install --no-deps --no-build-isolation -e "${ACT_OUTPUTS}/RoboTwin/XPolicyLab/policy/ACT/detr"
python -m pip check
