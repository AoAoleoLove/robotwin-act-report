#!/usr/bin/env bash
# Usage: source /absolute/path/to/outputs/activate-robotwin.sh
_robotwin_outputs="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_robotwin_outputs}/runtime/miniforge3/etc/profile.d/conda.sh"
conda activate RoboTwin
export CUDA_HOME="${_robotwin_outputs}/runtime/cuda128"
export PATH="${CUDA_HOME}/bin:${PATH}"
export CC=/usr/bin/gcc-14
export CXX=/usr/bin/g++-14
export CUB_HOME="${CUDA_HOME}/include"
export TORCH_CUDA_ARCH_LIST="12.0"
export MAX_JOBS=2
export HF_HOME="${_robotwin_outputs}/runtime/cache/huggingface"
export ROBOTWIN_RT_DENOISER=optix
cd "${_robotwin_outputs}/RoboTwin"
unset _robotwin_outputs
