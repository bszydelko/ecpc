import os
from globalSetup import *

def createFolder(f):
    if not os.path.exists(f):
        os.mkdir(f);
    return;


def main():
    
    depthFromBlenderPath = '1_renderedScene/depth/'
    depthFromGTParamsPath = '4_depthMaps/GT/'
    depthFromEstParamsPath = '4_depthMaps/Est/'
    resultsFilename = '5_evaluation/results.xlsx'
    
    createFolder('5_evaluation');
    
    import subprocess
    subprocess.call(['python', 'scripts/calcBadMatchedPixels.py', f'{width}', f'{height}', f'{num_of_cams}', depthFromBlenderPath, depthFromGTParamsPath, depthFromEstParamsPath, resultsFilename]);

if __name__ == '__main__':
    main()
