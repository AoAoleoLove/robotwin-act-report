# PyCharm 使用说明

已安装 JetBrains 官方稳定版 PyCharm 2026.2.3（build 262.10968.92），安装包 SHA256 校验通过。

在 Ubuntu 应用菜单搜索 **PyCharm – RoboTwin**，打开这个入口即可进入 RoboTwin 项目。它会加载现有 Conda 环境、CUDA 路径、OptiX 设置，并向 PyCharm 指定正确的 Python 解释器。已实测启动，IDE 日志确认识别了 Python 3.10.22 和现有软件包路径。

也可以在终端执行：

```bash
/home/leo/.local/bin/pycharm-robotwin
```

应用菜单中的普通 **PyCharm** 入口用于打开其他项目。

当前项目目录：

```text
/home/leo/Documents/Codex/2026-10-08/7-0-7-1/outputs/RoboTwin
```

当前 Python 解释器：

```text
/home/leo/Documents/Codex/2026-10-08/7-0-7-1/outputs/runtime/miniforge3/envs/RoboTwin/bin/python
```

使用左侧文件栏阅读代码、编辑 YAML 配置；使用底部 Terminal 终端执行安装、数据处理和训练命令。查看环境是否正常时，可以在终端运行：

```bash
python ../verify-robotwin-gpu.py
```

如果从普通 PyCharm 入口或其他应用打开项目，在运行仿真之前，于终端执行原有激活脚本：

```bash
source /home/leo/Documents/Codex/2026-10-08/7-0-7-1/outputs/activate-robotwin.sh
```

软件安装目录为 `/home/leo/.local/opt/pycharm-2026.2.3`，启动入口和用户设置均在你的用户目录下。本次使用已有 RoboTwin 环境，未重新安装 Python 或项目依赖。

PyCharm 的免费核心功能可以继续使用；Pro 功能的试用和许可遵循 JetBrains 的说明：[官方安装说明](https://www.jetbrains.com/help/pycharm/installation-guide.html)。专用启动入口采用官方支持的解释器环境变量：[官方配置说明](https://www.jetbrains.com/help/pycharm/configure-an-interpreter-using-command-line.html)。
