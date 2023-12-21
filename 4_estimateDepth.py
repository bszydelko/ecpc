import os
from globalSetup import *

def createFolder(f):
    if not os.path.exists(f):
        os.mkdir(f);
    return;


def main():
    
    backgndListFilename = '2_trackedMarker/backgndList.txt'
    paramsFromBlenderFilename = '1_renderedScene/scene_camparams.json'
    estimatedParamsFilename = '3_calibration/estimatedParams_it1.json'
    rescaledEstimatedParamsForEvaluationFilename = '3_calibration/estimatedParams_it1_forEvaluation.json'
    filenameListEstFilename = '4_depthMaps/filenames_estimatedParams.json'
    filenameListGTFilename = '4_depthMaps/filenames_groundTruthParams.json'
    
    createFolder('4_depthMaps');
    createFolder('4_depthMaps/GT');
    createFolder('4_depthMaps/Est');
    
    import subprocess
    subprocess.call(['python', 'scripts/rescaleParamsForEvaluation.py', paramsFromBlenderFilename, estimatedParamsFilename, rescaledEstimatedParamsForEvaluationFilename])
    subprocess.call(['python', 'scripts/createFilenameListsForIVDE.py', f'{width}', f'{height}', backgndListFilename, filenameListGTFilename, filenameListEstFilename]);    
    subprocess.call(['./DepthEstimator/ivde/build/Release/IVDE.exe', 'DepthEstimator/estimation_params.json', paramsFromBlenderFilename, filenameListGTFilename]);
    subprocess.call(['./DepthEstimator/ivde/build/Release/IVDE.exe', 'DepthEstimator/estimation_params.json', rescaledEstimatedParamsForEvaluationFilename, filenameListEstFilename]);

if __name__ == '__main__':
    main()
