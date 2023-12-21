import platform
import sys
import os
import argparse

import calibrator
import parameters

def calibrateCameras(args:list) -> bool:

    app = calibrator.Calibrator(args)
    app.run(iterations=2)
    return True

if __name__ == '__main__':
    print("PythonVer  = " + str(platform.python_version() ))
    print("PythonExe  = " + str(sys.executable            ))
    print("WorkingDir = " + str(os.getcwd()               ))
    print("ScriptPath = " + str(os.path.realpath(__file__)))
    print("\n")
    print("ARGC={} ARGV={}\n".format(len(sys.argv), str(sys.argv)))

    # Processing commandline
    argParser = argparse.ArgumentParser(prog="calibrateCameras.py")
    requiredArgs = argParser.add_argument_group('required arguments')
    requiredArgs.add_argument("-ncams",     type=int, required=True, help="Number of all cameras")
    requiredArgs.add_argument('-camrange',  type=str, required=True, help="Cameras to calibrate, <start:step:stop> or <[0,1,2,...]>")
    requiredArgs.add_argument('-npoints',   type=int, required=True, help="Numers of calibrating points to use")
    requiredArgs.add_argument('-r',         type=str, required=True, help="Path to txt file with reference points")
    requiredArgs.add_argument('-i',         type=str, required=True, help='Initial parameters file (json)')
    requiredArgs.add_argument('-o',         type=str, required=True, help="Path to output txt file with calibrated params")

    args = argParser.parse_args()
  
    # processing
    result = calibrateCameras(args)

    if(not result):
        print("Exiting with EXIT_FAILURE", file=sys.stdout)
        print("Exiting with EXIT_FAILURE", file=sys.stderr)
        sys.exit(1)
    else:     
        print("Exiting with EXIT_SUCCESS", file=sys.stdout)
        sys.exit(0)