import os
import glob

def main():
    for file in glob.glob('1_renderedScene/depth/*.png'):
        os.remove(file);
    for file in glob.glob('1_renderedScene/texture/*mp4'):
        os.remove(file);   

if __name__ == '__main__':
    main()
