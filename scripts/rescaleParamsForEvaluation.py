import json
import numpy as np
import argparse


def get_camera_positions_from_json(params_json):
    positions = {'x': [], 'y': [], 'z': []}
    for camera in params_json['cameras']:
        position = camera['Position']

        positions['x'].append(position[0])
        positions['y'].append(position[1])
        positions['z'].append(position[2])

    return positions

def calculate_relative_positions(absolute):
    relative = {'x': [], 'y': [], 'z': []}

    for abs in absolute['x']:
        relative['x'].append(abs - absolute['x'][0])

    for abs in absolute['y']:
        relative['y'].append(abs - absolute['y'][0])

    for abs in absolute['z']:
        relative['z'].append(abs - absolute['z'][0])
    
    return relative

def calculate_positive_positions(positions, offset):
    positive = {'x': [], 'y': [], 'z': []}

    for pos in positions['x']:
        positive['x'].append(pos + abs(offset['x']))

    for pos in positions['y']:
        positive['y'].append(pos + abs(offset['y']))

    for pos in positions['z']:
        positive['z'].append(pos + abs(offset['z']))

    return positive

def calculate_precent_of_magnitude(positions, mag):
    percent = {'x': [], 'y': [], 'z': []}

    for pos in positions['x']:
        percent['x'].append(pos / mag['x'])

    for pos in positions['y']:
        percent['y'].append(pos / mag['y'])

    for pos in positions['z']:
        percent['z'].append(pos / mag['z'])

    return percent

def main():

    ArgParser = argparse.ArgumentParser()
    ArgParser.add_argument('gt_params', help='Ground truth parameters')
    ArgParser.add_argument('est_params', help='Calibrated parameters')
    ArgParser.add_argument('rescaled_est_params_for_eval', help='Rescaled parameters for evaluation')
    Args = ArgParser.parse_args()

    gt_params_fname = Args.gt_params
    
    with open(gt_params_fname, 'r') as f:
        gt_params_json = json.load(f)
        gt_params_absolute_positions = get_camera_positions_from_json(gt_params_json)
        gt_params_relative_positions = calculate_relative_positions(gt_params_absolute_positions)

        gt_rel_min = { \
            'x': min(gt_params_relative_positions['x']), \
            'y': min(gt_params_relative_positions['y']), \
            'z': min(gt_params_relative_positions['z'])}
        
        gt_rel_max = { \
            'x': max(gt_params_relative_positions['x']), \
            'y': max(gt_params_relative_positions['y']), \
            'z': max(gt_params_relative_positions['z'])}
        
        gt_rel_mag = { \
            'x': abs(gt_rel_max['x'] - gt_rel_min['x']), \
            'y': abs(gt_rel_max['y'] - gt_rel_min['y']), \
            'z': abs(gt_rel_max['z'] - gt_rel_min['z'])}

        gt_params_positive_positions = calculate_positive_positions(gt_params_relative_positions, gt_rel_min) 
        #save gt_params_positive
        #print(gt_params_positive_positions)

    for idx, pos in enumerate(gt_params_positive_positions['x']):
        gt_params_json['cameras'][idx]['Position'][0] = pos

    for idx, pos in enumerate(gt_params_positive_positions['y']):
        gt_params_json['cameras'][idx]['Position'][1] = pos

    for idx, pos in enumerate(gt_params_positive_positions['z']):
        gt_params_json['cameras'][idx]['Position'][2] = pos

    
    est_params_fname = Args.est_params

    
    with open(est_params_fname, 'r') as f:
        rescaled_est_params_json = json.load(f)
        rescaled_est_params_absolute_positions = get_camera_positions_from_json(rescaled_est_params_json)
        rescaled_est_params_relative_positions = calculate_relative_positions(rescaled_est_params_absolute_positions)

        rescaled_est_rel_min = { \
            'x': min(rescaled_est_params_relative_positions['x']), \
            'y': min(rescaled_est_params_relative_positions['y']), \
            'z': min(rescaled_est_params_relative_positions['z'])}

        rescaled_est_rel_max = { \
            'x': max(rescaled_est_params_relative_positions['x']), \
            'y': max(rescaled_est_params_relative_positions['y']), \
            'z': max(rescaled_est_params_relative_positions['z'])}

        rescaled_est_rel_mag = { \
            'x': abs(rescaled_est_rel_max['x'] - rescaled_est_rel_min['x']), \
            'y': abs(rescaled_est_rel_max['y'] - rescaled_est_rel_min['y']), \
            'z': abs(rescaled_est_rel_max['z'] - rescaled_est_rel_min['z'])}

        rescaled_est_params_positive = calculate_positive_positions(rescaled_est_params_relative_positions, rescaled_est_rel_min) 
        rescaled_est_params_percentage_of_magnitude = calculate_precent_of_magnitude(rescaled_est_params_positive, rescaled_est_rel_mag)

        rescaled_est_params_new_positions = {'x': [], 'y': [], 'z': []}

        for perc in rescaled_est_params_percentage_of_magnitude['x']:
            rescaled_est_params_new_positions['x'].append(perc * gt_rel_mag['x'])

        for perc in rescaled_est_params_percentage_of_magnitude['y']:
            rescaled_est_params_new_positions['y'].append(perc * gt_rel_mag['y'])

        for perc in rescaled_est_params_percentage_of_magnitude['z']:
            rescaled_est_params_new_positions['z'].append(perc * gt_rel_mag['z'])


        for idx, pos in enumerate(rescaled_est_params_new_positions['x']):
            rescaled_est_params_json['cameras'][idx]['Position'][0] = pos

        for idx, pos in enumerate(rescaled_est_params_new_positions['y']):
            rescaled_est_params_json['cameras'][idx]['Position'][1] = pos

        for idx, pos in enumerate(rescaled_est_params_new_positions['z']):
            rescaled_est_params_json['cameras'][idx]['Position'][2] = pos

        with open(Args.rescaled_est_params_for_eval, 'w') as f:
            json.dump(rescaled_est_params_json, f, indent=4)


 


if __name__ == '__main__':
    main()