"""Run after sourcing activate-robotwin.sh. Checks real CUDA kernels and rendering."""
from pathlib import Path
import json
import os
import numpy as np
import torch

out_dir = Path(__file__).resolve().parent / "robotwin-install-logs"
report = {"torch": torch.__version__, "cuda": torch.version.cuda}
assert torch.cuda.is_available(), "CUDA unavailable"
report["gpu"] = torch.cuda.get_device_name(0)
x = torch.randn(512, 512, device="cuda")
y = x @ x.T
torch.cuda.synchronize()
assert torch.isfinite(y).all()
print("CUDA matrix multiplication passed:", report, flush=True)

from pytorch3d.ops import sample_farthest_points
points, indices = sample_farthest_points(torch.rand(1, 2048, 3, device="cuda"), K=128)
torch.cuda.synchronize()
assert points.shape == (1, 128, 3) and indices.unique().numel() == 128
report["pytorch3d_cuda_fps"] = True
print("PyTorch3D CUDA farthest-point sampling passed", flush=True)

from curobo.cuda_robot_model.cuda_robot_model import CudaRobotModel
from curobo.types.base import TensorDeviceType
from curobo.types.robot import RobotConfig
from curobo.util_file import get_robot_path, join_path, load_yaml
tensor_args = TensorDeviceType()
cfg = load_yaml(join_path(get_robot_path(), "franka.yml"))["robot_cfg"]
robot = CudaRobotModel(RobotConfig.from_dict(cfg, tensor_args).kinematics)
state = robot.get_state(torch.zeros((2, robot.get_dof()), **tensor_args.as_torch_dict()))
torch.cuda.synchronize()
assert torch.isfinite(state.ee_position).all()
report["curobo_cuda_kinematics"] = True
print("CuRobo CUDA forward kinematics passed", flush=True)

import sapien.core as sapien
from PIL import Image
sapien.render.set_camera_shader_dir("rt")
sapien.render.set_ray_tracing_samples_per_pixel(8)
sapien.render.set_ray_tracing_path_depth(4)
sapien.render.set_ray_tracing_denoiser(os.environ.get("ROBOTWIN_RT_DENOISER", "oidn"))
engine = sapien.Engine()
renderer = sapien.SapienRenderer()
engine.set_renderer(renderer)
scene = engine.create_scene()
scene.add_ground(0)
scene.set_ambient_light([0.3, 0.3, 0.3])
scene.add_directional_light([0, 1, -1], [1, 1, 1], shadow=True)
builder = scene.create_actor_builder()
builder.add_box_collision(half_size=[0.2, 0.2, 0.2])
builder.add_box_visual(half_size=[0.2, 0.2, 0.2], material=[0.8, 0.1, 0.1])
actor = builder.build(name="verification-box")
actor.set_pose(sapien.Pose([0, 0, 0.2]))
camera = scene.add_camera("verification", 640, 480, 1.0, 0.1, 100)
theta = np.arctan2(0.8, 2)
camera.set_pose(sapien.Pose([-2, 0, 1], [np.cos(theta/2), 0, np.sin(theta/2), 0]))
for _ in range(10):
    scene.step()
scene.update_render()
camera.take_picture()
rgb = camera.get_picture("Color")[..., :3]
assert np.isfinite(rgb).all() and rgb.std() > 0.01, "Invalid or blank render"
Image.fromarray((np.clip(rgb, 0, 1)*255).astype(np.uint8)).save(out_dir / "sapien-rt-test.png")
report["sapien_ray_tracing"] = True
report["denoiser"] = sapien.render.get_ray_tracing_denoiser()
(out_dir / "gpu-verification.json").write_text(json.dumps(report, indent=2))
print("SAPIEN ray tracing and camera capture passed", flush=True)
