import argparse

def main():
    ArgParser = argparse.ArgumentParser()
    ArgParser.add_argument('paramsFromBlenderFilename', help='paramsFromBlenderFilename')
    ArgParser.add_argument('initialParamsFilename', help='initialParamsFilename')
    Args = ArgParser.parse_args()
    
    print('Copy intrinsic parameters from blender');
    blenderFile = open(Args.paramsFromBlenderFilename);
    initialCalibrationParams = open(Args.initialParamsFilename, 'w');
    
    counter = -1;
    print('Clear extrinsic parameters and initialize extrinsics with linear arrangement');
    while True:
        line = blenderFile.readline();
        if not line:
            break;
        
        outLine = line;
        
        if '"Name":' in line:
            counter = counter + 1;
            outLine = '            "Name": "v' + str(counter) + '",\n';
        
        if '"Position":' in line:  
            
            #SKIP POSITION (camera extrinsics)
            for i in range (0,4,1):
                blenderFile.readline();
            
            #INIT POSITION (camera extrinsics) with vector [v,0,0] (initialize by linear arrangement)
            outLine = line \
            + '                ' + str(counter) + ',\n' \
            + '                0,\n' \
            + '                0\n' \
            + '            ],\n';
        
        if '"Rotation":' in line:                        
            #SKIP POSITION (camera extrinsics)
            for i in range (0,4,1):
                blenderFile.readline();    
                
            #INIT ROTATION (camera extrinsics) with vector [0,0,0] (initialize by linear arrangement)
            outLine = line \
            + '                0,\n' \
            + '                0,\n' \
            + '                0\n' \
            + '            ],\n';
            
        
        initialCalibrationParams.write(outLine);
    
    blenderFile.close();
    initialCalibrationParams.close();

if __name__ == '__main__':
    main()
