"""Convert XPolicyLab/RoboTwin trajectories to ACT, decoding through the shared codec."""
import argparse
import hashlib
import json
from pathlib import Path
import re

import cv2
import h5py
import numpy as np
from XPolicyLab.utils.process_data import pack_robot_state, get_robot_action_dim_info, decode_image_bit

ACT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = Path(__file__).resolve().parents[4]
CAMERA_NAMES = ['cam_head', 'cam_right_wrist', 'cam_left_wrist']


def convert_episode(source, destination, action_type, robot_info, env_cfg_type, is_sim):
    if destination.exists():
        raise FileExistsError(f'Already converted: {destination}; use a new --save-dir.')
    temporary = destination.with_suffix('.hdf5.partial')
    with h5py.File(source, 'r') as raw:
        data = {group: {name: value[()] for name, value in raw[group].items()}
                for group in ['state', 'action']}
        qpos = pack_robot_state(data, action_type, robot_info, source_type='dataset', state_type='state').astype(np.float32)
        actions = pack_robot_state(data, action_type, robot_info, source_type='dataset', state_type='action').astype(np.float32)
        if qpos.ndim != 2 or qpos.shape != actions.shape or not len(qpos):
            raise ValueError(f'Invalid state/action shapes: {source}: {qpos.shape}, {actions.shape}')
        if not np.isfinite(qpos).all() or not np.isfinite(actions).all():
            raise ValueError(f'Non-finite state/action: {source}')
        steps = len(qpos)
        for camera in CAMERA_NAMES:
            if len(raw[f'vision/{camera}/colors']) != steps:
                raise ValueError(f'Image/action length mismatch: {source}: {camera}')
        with h5py.File(temporary, 'w') as output:
            output.attrs['sim'] = is_sim
            output.attrs['source_path'] = str(source)
            output.attrs['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
            output.attrs['env_cfg_type'] = env_cfg_type
            output.attrs['action_type'] = action_type
            output.attrs['color_order'] = 'RGB'
            output.create_dataset('action', data=actions)
            observations = output.create_group('observations')
            observations.create_dataset('qpos', data=qpos)
            images = observations.create_group('images')
            for camera in CAMERA_NAMES:
                frames = images.create_dataset(camera, (steps, 480, 640, 3), dtype=np.uint8,
                                               chunks=(1, 480, 640, 3), compression='lzf')
                for step in range(steps):
                    image = decode_image_bit(raw[f'vision/{camera}/colors'][step])
                    if image is None or image.ndim != 3 or image.shape[-1] != 3:
                        raise ValueError(f'Invalid RGB image: {source}, {camera}, frame {step}')
                    frames[step] = cv2.resize(image, (640, 480))
    temporary.replace(destination)
    return steps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bench_name')
    parser.add_argument('ckpt_name')
    parser.add_argument('env_cfg_type')
    parser.add_argument('action_type', choices=['joint', 'ee'])
    parser.add_argument('--raw-dir', type=Path, help='Robot directory containing data/episode_*.hdf5')
    parser.add_argument('--save-dir', type=Path, help='Directory for converted episodes')
    source_type = parser.add_mutually_exclusive_group()
    source_type.add_argument('--sim', dest='is_sim', action='store_true', help='Mark as simulation data')
    source_type.add_argument('--real', dest='is_sim', action='store_false', help='Mark as real-robot data')
    parser.set_defaults(is_sim=None)
    args = parser.parse_args()
    is_sim = args.is_sim if args.is_sim is not None else args.bench_name == 'RoboTwin'
    raw_dir = (args.raw_dir or WORKSPACE_DIR / 'data' / args.bench_name / args.ckpt_name / args.env_cfg_type).resolve()
    save_dir = (args.save_dir or ACT_DIR / 'processed_data' / args.bench_name / args.ckpt_name /
                f'{args.env_cfg_type}-{args.action_type}').resolve()
    sources = sorted((raw_dir / 'data').glob('episode_*.hdf5'),
                     key=lambda path: int(re.fullmatch(r'episode_(\d+)\.hdf5', path.name).group(1)))
    if not sources:
        raise FileNotFoundError(f'No HDF5 episodes under {raw_dir / "data"}')
    if any(save_dir.glob('episode_*.hdf5')):
        raise FileExistsError(f'{save_dir} already contains episodes. Use a new --save-dir.')
    robot_info = get_robot_action_dim_info(args.env_cfg_type)
    save_dir.mkdir(parents=True, exist_ok=True)
    lengths = []
    for index, source in enumerate(sources):
        length = convert_episode(source, save_dir / f'episode_{index}.hdf5', args.action_type,
                                 robot_info, args.env_cfg_type, is_sim)
        lengths.append(length)
        print(f'ACT: converted {index + 1}/{len(sources)} episodes ({length} frames)', flush=True)
    config_path = ACT_DIR / 'TASK_CONFIGS.json'
    configs = json.loads(config_path.read_text()) if config_path.exists() else {}
    key = f'{args.bench_name}-{args.ckpt_name}-{args.env_cfg_type}-{args.action_type}'
    configs[key] = dict(dataset_dir=str(save_dir), num_episodes=len(sources),
                        episode_len=max(lengths), camera_names=CAMERA_NAMES)
    temporary_config = config_path.with_suffix('.json.partial')
    temporary_config.write_text(json.dumps(configs, indent=4) + '\n')
    temporary_config.replace(config_path)
    print(f'Wrote {key} to {config_path}', flush=True)


if __name__ == '__main__':
    main()
