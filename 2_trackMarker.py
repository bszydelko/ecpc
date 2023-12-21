import os
from globalSetup import *

def createFolder(f):
    if not os.path.exists(f):
        os.mkdir(f);
    return;

def main():
    
    seqListFilename = '2_trackedMarker/seqList.txt'
    backgndListFilename = '2_trackedMarker/backgndList.txt'
    markerPosFilename = '2_trackedMarker/markerPositions.txt'

    numFrames = ((end_frame-start_frame)//step_frame+1)
    
    createFolder('2_trackedMarker');
    
    import subprocess
    subprocess.call(['python', 'scripts/makeYUVLists.py', seqListFilename, backgndListFilename]);
    subprocess.call(['./MarkerTracker/build/Release/MarkerTracker.exe', '--nseq', f'{num_of_cams}', '--nframes', f'{numFrames}', '--seq', seqListFilename, '--mask', backgndListFilename, '--w', f'{width}', '--h', f'{height}', '--cs', '420', '--out', markerPosFilename]);

if __name__ == '__main__':
    main()
