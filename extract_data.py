# -*- coding: utf-8 -*-
"""
Created on Wed Jan 13 18:42:32 2021

@author: Christian Konstantinov
"""
import os
import json
from glob import glob

DATA_PATH = './dataset/osu'
RAW_PATH = f'{DATA_PATH}/raw'
EXTRACT_PATH = f'{DATA_PATH}/extracted'

def write_json(name):
    OSU_X = 640 # max Osupixel x value
    OSU_Y = 480 # max Osupixel y value
    MAP_PATH = f'{RAW_PATH}/{name}'
    FOLDER_PATH = f'{DATA_PATH}/extracted/{name}'
    JSON_FILE_PATH = f'{FOLDER_PATH}/beatmap.json'

    out_data = {'name': name, 'onsets': [], 'xs': [], 'ys': []}

    # read the raw data
    with open(glob(f'{MAP_PATH}/*.osu')[0], 'r', encoding='utf-8') as f:
        flag = False
        for line in f:
            if flag:
                data = line.split(',')
                out_data['onsets'].append(int(data[2])/1000)
                out_data['xs'].append(int(data[0])/OSU_X)
                out_data['ys'].append(int(data[1])/OSU_Y)
                continue
            if '[HitObjects]' in line:
                flag = True

    # write to json
    with open(JSON_FILE_PATH, 'w+') as f:
        json.dump(out_data, f)

def extract():
    """Extract all the data from the osu folder."""
    for dir in glob(f'{RAW_PATH}/*/'):
        name = dir.split('raw\\')[1][:-1]
        path = f'{EXTRACT_PATH}/{name}'
        if not os.path.exists(path):
            os.makedirs(path)
        write_json(name)

#%%

if __name__ == '__main__':
    extract()