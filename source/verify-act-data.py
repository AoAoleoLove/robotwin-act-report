"""Verify converted demonstrations, temporal alignment, loader and ACT GPU loss."""
import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch
import cv2
import h5py
import numpy as np
import torch
from PIL import Image, ImageDraw
from XPolicyLab.policy.ACT.constants import TASK_CONFIGS
from XPolicyLab.policy.ACT.utils import load_data, EpisodicDataset
from XPolicyLab.policy.ACT.detr.main import get_args_parser
from XPolicyLab.policy.ACT.detr.act_policy import ACTPolicy
from XPolicyLab.utils.process_data import pack_robot_state, get_robot_action_dim_info, decode_image_bit

outputs = Path(__file__).resolve().parent
key = 'RoboTwin-beat_block_hammer-aloha_agilex-joint'
config = TASK_CONFIGS[key]
dataset = Path(config['dataset_dir'])
manifest = json.loads((outputs / 'act-raw-data-manifest.json').read_text())
robot_info = get_robot_action_dim_info('aloha_agilex')
action_dim = sum(robot_info['arm_dim']) + sum(robot_info['ee_dim'])
lengths = []
for index, item in enumerate(manifest):
    source = Path(item['file'])
    assert hashlib.sha256(source.read_bytes()).hexdigest() == item['sha256'], source
    with h5py.File(source) as raw, h5py.File(dataset / f'episode_{index}.hdf5') as processed:
        assert bool(processed.attrs['sim'])
        data = {g: {name: field[()] for name, field in raw[g].items()} for g in ['state', 'action']}
        for group, target in [('state', 'observations/qpos'), ('action', 'action')]:
            expected = pack_robot_state(data, 'joint', robot_info, source_type='dataset', state_type=group).astype(np.float32)
            np.testing.assert_array_equal(processed[target][()], expected)
            assert np.isfinite(expected).all()
        length = len(processed['action'])
        lengths.append(length)
        for camera in config['camera_names']:
            images = processed[f'observations/images/{camera}']
            assert images.shape == (length, 480, 640, 3) and images.dtype == np.uint8
            for frame in [0, length // 2, length - 1]:
                expected = cv2.resize(decode_image_bit(raw[f'vision/{camera}/colors'][frame]), (640, 480))
                np.testing.assert_array_equal(images[frame], expected)
assert len(lengths) == config['num_episodes'] == 50
np.random.seed(0)
train, val, stats, is_sim = load_data(str(dataset), config['num_episodes'], config['camera_names'], 2, 2)
assert is_sim is True
# Ensure simulation data takes action[t:], not the real-robot action[t-1:] branch.
single = EpisodicDataset([0], str(dataset), config['camera_names'], stats, max(lengths))
with patch('numpy.random.choice', return_value=5):
    _, qpos, actions, pad = single[0]
with h5py.File(dataset / 'episode_0.hdf5') as f:
    expected = (f['action'][5:] - stats['action_mean']) / stats['action_std']
    np.testing.assert_allclose(actions[:len(expected)].numpy(), expected)
    assert (~pad).sum().item() == len(expected)
    preview = Image.new('RGB', (640 * 3, 510), 'white')
    labels = ImageDraw.Draw(preview)
    for index, camera in enumerate(config['camera_names']):
        preview.paste(Image.fromarray(f[f'observations/images/{camera}'][len(f['action']) // 2]), (index * 640, 30))
        labels.text((index * 640 + 10, 8), camera, fill='black')
    preview.save(outputs / 'act-data-preview.png')
images, qpos, actions, pad = next(iter(train))
val_images, _, _, _ = next(iter(val))
assert tuple(images.shape) == (2, 3, 3, 480, 640)
assert torch.isfinite(images).all() and torch.isfinite(qpos).all() and torch.isfinite(actions).all()
os.environ['ACT_ACTION_DIM'] = str(action_dim)
cfg = get_args_parser().parse_args([
    '--ckpt_dir', str(outputs / 'act-data-unused-checkpoints'), '--policy_class', 'ACT',
    '--bench_name', 'RoboTwin', '--task_name', 'beat_block_hammer', '--seed', '0', '--num_epochs', '1',
])
for name, value in dict(lr=1e-5, lr_backbone=1e-5, backbone='resnet18', kl_weight=10,
                        chunk_size=50, hidden_dim=512, dim_feedforward=3200,
                        enc_layers=4, dec_layers=7, nheads=8, camera_names=config['camera_names']).items():
    setattr(cfg, name, value)
torch.set_num_threads(4)
torch.manual_seed(0)
torch.cuda.reset_peak_memory_stats()
policy = ACTPolicy({'kl_weight': 10}, cfg)
policy.train()
losses = policy(qpos.cuda(), images.cuda(), actions.cuda(), pad.cuda())
assert torch.isfinite(losses['loss'])
losses['loss'].backward()
assert all(torch.isfinite(p.grad).all() for p in policy.parameters() if p.grad is not None)
torch.cuda.synchronize()
report = dict(task=key, episodes=len(lengths), total_frames=sum(lengths), min_frames=min(lengths), max_frames=max(lengths),
              train_episodes=len(train.dataset), validation_episodes=len(val.dataset), raw_files_unchanged=True,
              state_action_exact_match=True, sampled_rgb_exact_match=True, simulation_alignment='action[t:] verified',
              image_batch_shape=list(images.shape), action_batch_shape=list(actions.shape),
              losses={k: v.detach().cpu().item() for k, v in losses.items()},
              gpu=torch.cuda.get_device_name(), torch=torch.__version__,
              peak_allocated_mib=torch.cuda.max_memory_allocated() / 2**20,
              gpu_forward_backward='passed; no optimizer update, no task training checkpoint created',
              processed_bytes=sum(p.stat().st_size for p in dataset.glob('*.hdf5')), dataset_dir=str(dataset))
(outputs / 'act-data-verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
