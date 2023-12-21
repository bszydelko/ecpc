import glob
import argparse

def main():
    ArgParser = argparse.ArgumentParser()
    ArgParser.add_argument('seqListFilename', help='seqListFilename')
    ArgParser.add_argument('backgndListFilename', help='backgndListFilename')
    Args = ArgParser.parse_args()
    
    seqListFilename = Args.seqListFilename
    backgndListFilename = Args.backgndListFilename
    
    seqList = open(seqListFilename, 'w')
    backgndList = open(backgndListFilename, 'w')
    
    for filename in glob.glob('1_renderedScene/texture/*texture*.yuv'):
        seqList.write(filename + '\n');
    for filename in glob.glob('1_renderedScene/texture/*background*.yuv'):
        backgndList.write(filename + '\n');     

if __name__ == '__main__':
    main()
