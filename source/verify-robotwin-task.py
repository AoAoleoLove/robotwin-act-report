"""Load the guide's task and capture its RGB cameras without collecting a dataset."""
from pathlib import Path
import sys
import json
import yaml
import numpy as np
from PIL import Image

root = Path.cwd()
sys.path.insert(0, str(root))
from envs.beat_block_hammer import beat_block_hammer

args = yaml.safe_load((root / "env_cfg/task_config/demo_clean.yml").read_text())
embodiments = yaml.safe_load((root / "env_cfg/task_config/_embodiment_config.yml").read_text())
robot_dir = (root / embodiments["aloha-agilex"]["file_path"]).resolve()
config = yaml.safe_load((robot_dir / "config.yml").read_text())
args.update(task_name="beat_block_hammer", task_config="demo_clean", seed=0,
            left_robot_file=str(robot_dir), right_robot_file=str(robot_dir),
            left_embodiment_config=config, right_embodiment_config=config,
            dual_arm_embodied=True, embodiment_name="aloha-agilex",
            now_ep_num=0, render_freq=0, save_data=False, collect_data=False)
task = beat_block_hammer()
task.setup_demo(**args)
obs = task.get_obs()
out = Path(__file__).resolve().parent / "robotwin-install-logs"
shapes = {}
for name, camera in obs["observation"].items():
    if "rgb" not in camera:
        continue
    rgb = np.asarray(camera["rgb"])
    assert rgb.ndim == 3 and rgb.shape[2] == 3 and rgb.std() > 1, (name, rgb.shape)
    shapes[name] = list(rgb.shape)
    Image.fromarray(rgb.astype(np.uint8)).save(out / f"beat_block_hammer-{name}.png")
assert "head_camera" in shapes and len(shapes) >= 3, shapes
assert np.isfinite(obs["joint_action"]["vector"]).all()
(out / "task-verification.json").write_text(json.dumps({"task": "beat_block_hammer",
    "config": "demo_clean", "embodiment": "aloha-agilex", "rgb_shapes": shapes,
    "joint_shape": list(obs["joint_action"]["vector"].shape)}, indent=2))
print("RoboTwin task, dual-arm planners, physics, and RGB cameras passed:", shapes, flush=True)
task.close_env()
