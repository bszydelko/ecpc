import os
import subprocess

from globalSetup import *

def createFolder(f):
    if not os.path.exists(f): os.mkdir(f)
    return

def main():
    sceneFilename = 'TestScene/scene.blend'
    
    createFolder('1_renderedScene');
    
    
    subprocess.call(['blender', sceneFilename, '--python', 'scripts/renderBlenderMVD.py', '--', '-s', f'{start_frame}', '-e', f'{end_frame}', '-j', f'{step_frame}', '-zn', f'{znear}', '-zf', f'{zfar}'], shell=True )
    subprocess.call(['python', 'scripts/convertPNG2YUV.py', f'{start_frame}', f'{end_frame}', f'{step_frame}', f'{width}', f'{height}', f'{num_of_cams}'], shell=True)
    subprocess.call(['python', 'scripts/convertMP42YUV.py', f'{start_frame}', f'{end_frame}', f'{step_frame}', f'{width}', f'{height}', f'{num_of_cams}'], shell=True)
    subprocess.call(['python', 'scripts/createBackground.py', f'{start_frame}', f'{end_frame}', f'{step_frame}', f'{width}', f'{height}', f'{num_of_cams}'], shell=True)
    subprocess.call(['python', 'scripts/removePNGandYUV.py'])

if __name__ == '__main__':
    main()
