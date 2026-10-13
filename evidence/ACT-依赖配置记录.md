# ACT 依赖配置记录

本次只完成 ACT 的环境配置和运行验证，没有开始正式任务训练或批量数据转换。

## 使用的环境

复用 RoboTwin 的 Python 3.10 环境，与 PyCharm 中的 RoboTwin 解释器一致：

`/home/leo/Documents/Codex/2026-10-08/7-0-7-1/outputs/runtime/miniforge3/envs/RoboTwin/bin/python`

保留 `torch==2.7.1+cu128`、`torchvision==0.22.1+cu128`、`numpy==1.26.4` 和 `scipy==1.10.1`。
PyTorch 官方版本页面列出了 2.7.1 / 0.22.1 的 CUDA 12.8 组合：
https://pytorch.org/get-started/previous-versions/

补充安装：

| 包 | 版本 | 用途 |
|---|---|---|
| einops | 0.8.1 | 整理图像和动作张量的维度 |
| rospkg | 1.5.1 | 原始 ACT 工具链使用的机器人软件包信息工具；不代表安装了完整 ROS |
| mujoco | 2.3.7 | 原始 ACT 工具链的物理仿真依赖 |
| dm-control | 1.0.14 | MuJoCo 的环境封装，按 ACT 原始要求安装 |
| detr | 0.0.0，本地可编辑安装 | ACT 内部的视觉和 Transformer 模型代码 |

其余依赖沿用已经安装的版本。XPolicyLab 已经以本地可编辑形式安装，无需重新安装。

## 如何进入 ACT 目录

在终端运行：

```bash
source /home/leo/Documents/Codex/2026-10-08/7-0-7-1/outputs/activate-act.sh
```

这会激活 RoboTwin 环境、设置显卡相关环境变量，并进入 ACT 目录。

不要直接运行仓库原始的 `install.sh` 或依据原始 `conda_env.yaml` 重建环境，前者固定了旧版 PyTorch，后者也是旧的 CUDA 配置。
本机使用的兼容安装入口是同目录下的 `install-act-rtx5070.sh`；它检查现有 PyTorch/CUDA 版本，并利用 `act-preserve-constraints.txt` 保护已有依赖。
已经安装完成，不需要再次运行安装。

## 验证结果

- `pip check`：没有依赖冲突。
- 安装前后对比：已有包的版本没有变化。
- ACT 训练入口和数据转换入口：均能加载并显示命令行帮助。
- MuJoCo 和 dm-control：均能创建小型物理场景并推进一步。
- RTX 5070：ACT 完成前向计算、反向传播、优化器更新和推理。
- 测试输入：单批、三路 640×480 RGB 图像、14 维动作；输出形状为 `[1, 50, 14]`。
- 模型结构按训练入口设置：ResNet18、hidden_dim=512、feedforward=3200、chunk_size=50、4 层编码器、7 层解码器。
- 单批测试峰值分配显存约 1509.5 MiB。正式训练还有数据加载、批大小等额外开销，不能据此直接确定 batch_size=16 可行。

验证脚本：`verify-act-gpu.py`；结果：`act-gpu-verification.json`；日志：`act-gpu-verification.log`。
当前环境版本快照：`act-requirements-lock.txt`。

## 下一步

本机已有 `data/demo_clean/beat_block_hammer/aloha_agilex/` 示例数据。
后续数据准备现已完成，详见同目录的 `ACT-数据准备记录.md`。
实际检查确认，原始数据的内部字段已经与共享工具兼容，需要衔接的是输入目录。
原始 `train.sh` 的根目录计算正确；现在增加了自动切换到 ACT 目录和遇错停止的处理。
下一步是先用小批次进行短训练验证，再决定正式训练的参数。
