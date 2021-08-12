# -*- coding: utf-8 -*-
"""
Created on Thu Jan 14 14:35:39 2021

@author: Christian Konstantinov
"""

from glob import glob
import json
from librosa import load, time_to_frames

import torch
from torchaudio import transforms

from folder_iterator import iterate_folder
from hyperparameters import DSP

DATA_PATH = './dataset/osu'
RAW_PATH = f'{DATA_PATH}/raw'
EXTRACT_PATH = f'{DATA_PATH}/extracted'

from functools import wraps
from time import time

def measure(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time()
        result = f(*args, **kwargs)
        end = time()
        print('Elapsed time: {} ms'.format((end-start) * 1000))
        return result
    return wrapper

# TODO: Move extraction to dataset for easy parallelization?

@measure
def extract() -> None:
    """Extract all the data from the osu folder."""
    dsp = DSP()
    for name in iterate_folder(RAW_PATH):
        song_path = f'{EXTRACT_PATH}/{name}'
        tensor, indices = extract_features(name, dsp)
        targets = create_onset_labels(tensor, song_path, dsp)
        torch.save((tensor, indices), f'{song_path}/features.pt')
        torch.save(targets, f'{song_path}/targets.pt')

def extract_features(name: str, dsp: DSP) -> torch.Tensor:
    """Extract the spectrogams and tensor indices for the dataset."""
    tensor = get_lmfs(name, dsp)
    tensor = pad_tensor(tensor, tensor.shape[-1], dsp.context)
    indices = list(range(0, tensor.shape[-1] // dsp.context))
    return tensor, indices

def create_onset_labels(features: torch.Tensor, song_path: str, dsp: DSP):
    with open(f'{song_path}/beatmap.json', 'r') as f:
        beatmap = json.load(f)
    onsets = time_to_frames(beatmap['onsets'], sr=dsp.fs, hop_length=dsp.stride, n_fft=dsp.W)
    targets = torch.zeros(features.shape[2])
    for o in onsets:
        targets[o] = 1
    return targets

def get_lmfs(name: str, dsp: DSP) -> torch.Tensor:
    """Return the log mel frequency spectrogram."""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    map_path = f'{RAW_PATH}/{name}'

    mono_sig, fs = load(glob(f'{map_path}/*.mp3')[0], sr=dsp.fs, res_type='kaiser_fast')
    mono_sig = torch.from_numpy(mono_sig).to(device)
    norm_sig = normalize(mono_sig)

    mfs = transforms.MelSpectrogram(sample_rate=fs, n_fft=dsp.W,
                                    f_min=dsp.f_min, f_max=dsp.f_max,
                                    n_mels=dsp.bands, hop_length=dsp.stride,
                                    window_fn=torch.hamming_window).to(device)(norm_sig)

    lmfs = transforms.AmplitudeToDB().to(device)(mfs).unsqueeze(0)
    return lmfs

def pad_tensor(unpadded: torch.Tensor, size: int, W: int) -> torch.Tensor:
    pad_sig = torch.zeros(unpadded.shape[0], unpadded.shape[1], size + (W - (size % W)))
    pad_sig[:, :, :size] = unpadded
    return pad_sig

def normalize(tensor: torch.Tensor) -> torch.Tensor:
    """Return the tensor normalized to the interval [-1, 1] where μ = 0, σ² = 1."""
    minus_mean = tensor - tensor.float().mean()
    return minus_mean / minus_mean.abs().max()

def create_coordinate_labels():
    targets = []
    for name in iterate_folder(EXTRACT_PATH):
        path = f'{EXTRACT_PATH}/{name}'
        with open(f'{path}/beatmap.json', 'r') as f:
            beatmap = json.load(f)
        targets.append([beatmap['xs'], beatmap['ys']])

    # pad for training
    pad = max(len(coord[0]) for coord in targets)
    for i, t in enumerate(targets):
        for j in range(2):
            pad_len = pad-len(t[j])
            if pad_len != 0:
                t[j].extend([j]*(pad_len))
            t[j] = torch.tensor(t[j])
        targets[i] = torch.stack((t[0], t[1]))
    targets = torch.stack(targets)
    dataset = torch.full((len(targets), 2, pad), 0.0)
    dataset += targets

#%%
if __name__ == '__main__':
    extract()
