#!/usr/bin/env bash
# Usage: source /absolute/path/to/outputs/activate-act.sh
_act_outputs="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_act_outputs}/activate-robotwin.sh"
cd "${_act_outputs}/RoboTwin/XPolicyLab/policy/ACT"
unset _act_outputs
