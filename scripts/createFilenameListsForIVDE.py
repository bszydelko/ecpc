import argparse

def main():
    ArgParser = argparse.ArgumentParser()
    ArgParser.add_argument('width', help='width')
    ArgParser.add_argument('height', help='height')
    ArgParser.add_argument('inputSeq', help='inputSeq')
    ArgParser.add_argument('filenameListGTFilename', help='filenameListGTFilename')
    ArgParser.add_argument('filenameListEstFilename', help='filenameListEstFilename')
    Args = ArgParser.parse_args()
    
    seqList = open(Args.inputSeq);
    GTList = open(Args.filenameListGTFilename, 'w');
    EstList = open(Args.filenameListEstFilename, 'w');
    W = Args.width;
    H = Args.height;
    
    GTList.write('{\n  "filenames": [\n');
    EstList.write('{\n  "filenames": [\n');
        
    counter = -1;
    while True:
        line = seqList.readline();
        if not line:
            GTList.write('\n  ]\n}');
            EstList.write('\n  ]\n}');
            break;
           
        counter = counter + 1;
        if counter > 0:
            GTList.write(',\n');
            EstList.write(',\n');
        
        GTList.write('    {\n      "InputView": "./' + line[0:-1].replace('\\','/') + '",\n');
        EstList.write('    {\n      "InputView": "./' + line[0:-1].replace('\\','/') + '",\n');
        
        GTList.write('      "OutputDepthMap": "4_depthMaps/GT/v' + str(counter) + '_depth_' + W + 'x' + H + '_yuv420p16le.yuv"\n    }');
        EstList.write('     "OutputDepthMap": "4_depthMaps/Est/v' + str(counter) + '_depth_' + W + 'x' + H + '_yuv420p16le.yuv"\n    }');

if __name__ == '__main__':
    main()
