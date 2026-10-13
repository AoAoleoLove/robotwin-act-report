#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bench_name=$1
ckpt_name=$2
env_cfg_type=$3
action_type=$4

shift 4
python "${SCRIPT_DIR}/detr/process_data.py" "$bench_name" "$ckpt_name" "$env_cfg_type" "$action_type" "$@"
