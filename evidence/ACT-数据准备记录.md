# ACT 数据准备记录

## 已完成

任务是 `beat_block_hammer`，机器人是 `aloha_agilex`，动作类型是 `joint`。
原始数据共有 50 段示范、5682 个采样时刻，每段 108～125 个时刻。
每个时刻包含头部、右手腕、左手腕三路相机图像，以及左右机械臂和夹爪的状态与动作。

原始数据内部已经是共享工具支持的格式，无需改写原始文件的字段。
通过原始文件逐个 SHA256 校验，确认转换后原始文件没有变化。

原始目录：

`/home/leo/Documents/Codex/2026-10-08/7-0-7-1/outputs/RoboTwin/data/demo_clean/beat_block_hammer/aloha_agilex/`

ACT 数据目录：

`/home/leo/Documents/Codex/2026-10-08/7-0-7-1/outputs/RoboTwin/XPolicyLab/policy/ACT/processed_data/RoboTwin/beat_block_hammer/aloha_agilex-joint/`

转换结果共约 3.2 GiB。它比原始文件大，是因为原始图像保存为 JPEG 字节，而 ACT 需要可直接索引的 RGB 数组，并把图像调整为 640×480。
每帧用 HDF5 LZF 无损压缩保存。解码始终使用共享的 `decode_image_bit`，没有自行交换颜色通道。

训练配置已写入 ACT 的 `TASK_CONFIGS.json`，配置名：

`RoboTwin-beat_block_hammer-aloha_agilex-joint`

## 转换后每个文件的内容

| 字段 | 内容 |
|---|---|
| `action` | T×14 的目标动作 |
| `observations/qpos` | T×14 的当前关节状态 |
| `observations/images/cam_head` | T×480×640×3 的头部 RGB 图像 |
| `observations/images/cam_right_wrist` | 右手腕 RGB 图像 |
| `observations/images/cam_left_wrist` | 左手腕 RGB 图像 |

14 维由共享机器人工具读取配置得到，排列是左臂 6 维、左夹爪 1 维、右臂 6 维、右夹爪 1 维。
每个文件记录了 `sim=True`、原始文件路径、原始文件校验值、机器人配置和 RGB 颜色顺序。

## 调整的代码

- `detr/process_data.py`：支持显式 `--raw-dir`、可选 `--save-dir`，按真实文件名发现示范；逐帧转换、检查数据长度和数值；生成绝对路径训练配置，拒绝覆盖已有示范。
- `process_data.sh`：支持传递转换选项，使用脚本的绝对路径，因此从其他目录启动也能工作。
- `utils.py`：读取 `sim` 属性。仿真数据用动作序列 `action[t:]`，避免套用实机数据的 `action[t-1:]` 偏移。没有这个属性的旧文件继续使用原有实机逻辑。
- `train.sh`：自动切换到 ACT 目录、遇错停止。核对后保留了原本正确的根目录计算。
- ACT README：补充了下载数据的转换方法和仿真标记说明。

本次转换命令如下（已完成，不要重复运行到同一输出目录）：

```bash
source /home/leo/Documents/Codex/2026-10-08/7-0-7-1/outputs/activate-act.sh
bash process_data.sh RoboTwin beat_block_hammer aloha_agilex joint \
  --raw-dir /home/leo/Documents/Codex/2026-10-08/7-0-7-1/outputs/RoboTwin/data/demo_clean/beat_block_hammer/aloha_agilex
```

## 验证

- 全部 50 段状态与动作：与原始数据打包结果逐项完全一致。
- 每段每个相机的首帧、中间帧、末帧：与共享解码器输出完全一致。
- 仿真动作对齐：固定采样时刻验证了使用 `action[t:]`。
- ACT 原始数据加载器：成功读到训练批次和验证批次，按默认 80%/20% 比例分成 40/10 段。
- 实际数据在 RTX 5070 上：完成前向计算和反向传播，损失及梯度均为有限数值。
- 测试 batch_size=2，峰值分配显存约 1782.7 MiB。没有执行优化器更新，没有生成任务训练检查点。
- 训练启动脚本：从 `/tmp` 调用并拦截实际训练进程，验证能自动进入 ACT 目录、计算出动作维度 14、传递正确配置。此检查没有启动 6000 轮训练。

验证脚本：`verify-act-data.py`。结构化报告：`act-data-verification.json`。
三路图像预览：`act-data-preview.png`。原始文件清单：`act-raw-data-manifest.json`。

## 下一步

先进行少量轮次的真实训练，检查训练损失、验证损失、模型保存和加载是否正常。
当前原始 `train.sh` 仍默认 batch_size=16、6000 轮，不要直接用它启动长训练。
建议下一步从已验证的 batch_size=2 开始，先完成短训练检查，再测量并选择正式训练参数。
