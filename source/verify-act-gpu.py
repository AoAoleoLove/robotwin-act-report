"""Check ACT dependencies and one synthetic GPU optimizer step, without training a task."""
import os
os.environ.setdefault('MUJOCO_GL', 'egl')
import importlib
import json
from pathlib import Path
import torch
import torchvision
import mujoco
from dm_control import mujoco as dm_mujoco
from XPolicyLab.utils.process_data import get_robot_action_dim_info
from XPolicyLab.policy.ACT.detr.main import get_args_parser
from XPolicyLab.policy.ACT.detr.act_policy import ACTPolicy

outputs = Path(__file__).resolve().parent
assert torch.__version__ == '2.7.1+cu128', torch.__version__
assert torchvision.__version__ == '0.22.1+cu128', torchvision.__version__
assert torch.cuda.is_available()
for name in ['rospkg', 'einops', 'h5py', 'matplotlib', 'XPolicyLab.policy.ACT.model']:
    importlib.import_module(name)

xml = '<mujoco><worldbody><body><freejoint/><geom type="sphere" size="0.1"/></body></worldbody></mujoco>'
model = mujoco.MjModel.from_xml_string(xml)
mujoco.mj_step(model, mujoco.MjData(model))
physics = dm_mujoco.Physics.from_xml_string(xml)
physics.step()

robot_info = get_robot_action_dim_info('aloha_agilex')
action_dim = sum(robot_info['arm_dim']) + sum(robot_info['ee_dim'])
os.environ['ACT_ACTION_DIM'] = str(action_dim)
cfg = get_args_parser().parse_args([
    '--ckpt_dir', str(outputs / 'act-smoke-unused-checkpoints'),
    '--policy_class', 'ACT', '--bench_name', 'RoboTwin',
    '--task_name', 'synthetic_dependency_check', '--seed', '0', '--num_epochs', '1',
])
for key, value in dict(
    lr=1e-5, lr_backbone=1e-5, backbone='resnet18', kl_weight=10,
    chunk_size=50, hidden_dim=512, dim_feedforward=3200,
    enc_layers=4, dec_layers=7, nheads=8,
    camera_names=['cam_head', 'cam_right_wrist', 'cam_left_wrist'],
).items():
    setattr(cfg, key, value)
torch.set_num_threads(4)
torch.manual_seed(0)
torch.cuda.reset_peak_memory_stats()
policy = ACTPolicy({'kl_weight': 10}, cfg)
policy.train()
qpos = torch.randn(1, action_dim, device='cuda')
images = torch.rand(1, 3, 3, 480, 640, device='cuda')
actions = torch.randn(1, 50, action_dim, device='cuda')
is_pad = torch.zeros(1, 50, dtype=torch.bool, device='cuda')
optimizer = policy.configure_optimizers()
optimizer.zero_grad(set_to_none=True)
losses = policy(qpos, images, actions, is_pad)
assert torch.isfinite(losses['loss'])
losses['loss'].backward()
assert any(p.grad is not None for p in policy.parameters())
assert all(torch.isfinite(p.grad).all() for p in policy.parameters() if p.grad is not None)
optimizer.step()
policy.eval()
with torch.no_grad():
    predictions = policy(qpos, images)
assert tuple(predictions.shape) == (1, 50, action_dim), predictions.shape
assert torch.isfinite(predictions).all()
torch.cuda.synchronize()
report = {
    'test': 'synthetic ACT dependency/GPU check; not task training',
    'torch': torch.__version__, 'torchvision': torchvision.__version__,
    'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(),
    'action_dim': action_dim, 'input_shape': list(images.shape),
    'prediction_shape': list(predictions.shape),
    'losses': {k: float(v.detach().cpu()) for k, v in losses.items()},
    'peak_allocated_mib': torch.cuda.max_memory_allocated() / 2**20,
    'optimizer_step': 'passed', 'mujoco_step': 'passed', 'dm_control_step': 'passed',
}
(outputs / 'act-gpu-verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
