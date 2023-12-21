import os
from globalSetup import *

def createFolder(f):
    if not os.path.exists(f):
        os.mkdir(f);
    return;


def main():
    
    markerPosFilename = '2_trackedMarker/markerPositions.txt'
    paramsFromBlenderFilename = '1_renderedScene/scene_camparams.json'
    initialParamsFilename = '3_calibration/initialParams.json'
    estimatedParamsFilename = '3_calibration/estimatedParams.json'

    numFrames = ((end_frame-start_frame)//step_frame+1)
    
    createFolder('3_calibration');
    cameraRange = '0:1:'+str(num_of_cams - 1)
    
    import subprocess
    subprocess.call(['python', 'scripts/copyProperIntrinsicAndInitExtrinsicsBySomething.py', paramsFromBlenderFilename, initialParamsFilename]);
    subprocess.call(['python', 'Calibrator/calibrateCameras.py', '-ncams', f'{num_of_cams}', '-camrange', f'{cameraRange}', '-npoints', f'{numFrames}', '-r', markerPosFilename, '-i', initialParamsFilename, '-o', estimatedParamsFilename]);

if __name__ == '__main__':
    main()
