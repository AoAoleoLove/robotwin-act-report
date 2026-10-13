# RoboTwin 环境安装记录

2026-10-08 完成。按照 [RoboTwin 官方安装指南](https://robotwin-platform.github.io/doc/usage/robotwin-install.html) 安装了基础仿真环境、XPolicyLab、CuRobo、PyTorch3D 和全部官方资产。验收范围包括 GPU 运算、光线追踪、双臂规划器初始化，以及 `beat_block_hammer/demo_clean/aloha-agilex` 场景和相机；未进行批量数据采集或 ACT 训练。

以后打开终端，执行：

```bash
source /home/leo/Documents/Codex/2026-10-08/7-0-7-1/outputs/activate-robotwin.sh
```

脚本会激活 `RoboTwin` Conda 环境、配置 CUDA/编译器/OptiX，并进入 RoboTwin 根目录。Conda 安装在本项目的 `outputs/runtime/miniforge3`，CUDA 工具链在 `outputs/runtime/cuda128`。

| 项目 | 已安装版本 |
|---|---|
| 系统 / 内核 | Ubuntu 24.04 / 7.1.0-070100-generic |
| GPU / 驱动 | RTX 5070 12 GB / NVIDIA 580.178.04 open |
| Python | 3.10 |
| PyTorch / TorchVision | 2.7.1+cu128 / 0.22.1+cu128 |
| CUDA Toolkit | 12.8.1，nvcc 12.8.93 |
| NumPy / SciPy | 1.26.4 / 1.10.1 |
| SAPIEN / MPLib | 3.0.0b1 / 0.2.1 |
| CuRobo / Warp | 0.7.8 / 1.12.0 |
| PyTorch3D | 0.7.8，已编译 sm_120 CUDA 扩展 |
| XPolicyLab | 0.0.1，RoboTwin 固定的子模块提交 |

为 RTX 5070 做了必要的兼容调整：

- 使用支持 Blackwell 的 PyTorch CUDA 12.8 构建；实际检查确认包含 `sm_120`。依据：[PyTorch 2.7 官方说明](https://pytorch.org/blog/pytorch-2-7/)。
- 保留 NumPy 1.26.4，并限定 Zarr 2.x、MoviePy 1.x，以适配仓库现有依赖和接口。
- 按官方脚本应用 SAPIEN URDF/SRDF 文件的 UTF-8 修补，以及 MPLib 的 screw-plan 条件修补。
- SAPIEN 自带 OIDN 2.0.1 在本机报 `unsupported device type: CUDA`。激活脚本设置 `ROBOTWIN_RT_DENOISER=optix`，仓库 `envs/_base_task.py` 增加一处读取该变量的配置。OptiX 已实测正常，属于 [SAPIEN 官方支持的去噪器](https://sapien-sim.github.io/docs/user_guide/rendering/raytracing_renderer.html)。
- 将 Conda CUDA 的目标架构头文件以相对软链接补入工具链的 `include`，供 PyTorch 扩展构建使用。

官方资产 `embodiments`、`objects`、`background_texture` 全部下载并解压，合计约 16 GB。下载经过 SHA256 校验，解压检查 CRC，模型配置中的绝对路径已生成。压缩包在完成解压后清理。

验收全部通过：CUDA 矩阵运算、PyTorch3D GPU 最远点采样、CuRobo GPU 正向运动学、SAPIEN 光线追踪和 OptiX、锤子任务双臂规划器与物理场景、四路 320×240 RGB 图像、14 维关节状态，以及 `pip check`、`dpkg --audit`。尚存上游弃用提示，不影响这些检查。

如需复查，先执行激活命令，再运行：

```bash
python ../verify-robotwin-gpu.py
python ../verify-robotwin-task.py
python -m pip check
```

验收报告和图像在 `outputs/robotwin-install-logs/`：`gpu-verification.json`、`task-verification.json`、`task-verification-final.log`、`beat_block_hammer-head_camera.png` 等。Python 完整版本记录在 `outputs/robotwin-requirements-lock.txt`，Conda 精确记录在两个 `robotwin-conda-*-lock.txt` 文件中。

源码提交：RoboTwin `ea8b21121ebb3cd201ff5b3fe361944ac94eda3f`；XPolicyLab `fa431ecd893ee706883e64fe5fe1464ec8cd928d`；CuRobo `d64c4b005459db10c5dd867d8b30a87d5bda9bdb`；PyTorch3D `75ebeeaea0908c5527e7b1e305fbc7681382db47`。

后续 Part 2 将进入示范数据和 ACT 环节。ACT 的依赖安装需要继续保留适配 RTX 5070 的 PyTorch/CUDA 版本，训练显存用量和参数将单独验证。当前安装包含可编辑源码及绝对模型路径，移动安装目录后需要重建相应路径配置。
