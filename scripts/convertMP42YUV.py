import subprocess
import argparse

def main():
  ArgParser = argparse.ArgumentParser()
  ArgParser.add_argument('start_frame', help='start frame')
  ArgParser.add_argument('end_frame', help='end frame')
  ArgParser.add_argument('step_frame', help='step frame')
  ArgParser.add_argument('width', help='width')
  ArgParser.add_argument('height', help='height')
  ArgParser.add_argument('num_of_cams', help='num of cams')
  Args = ArgParser.parse_args()

  start_frame = int(Args.start_frame)
  end_frame   = int(Args.end_frame)
  step_frame  = int(Args.step_frame)
  width = Args.width
  height = Args.height
  num_of_cams = int(Args.num_of_cams)
  
  for CamIdx in range(0, num_of_cams):
    FFMPEG_Args = ['ffmpeg', "-i", f"1_renderedScene/texture/{start_frame:04d}-{end_frame:04d}.{CamIdx:03d}.mp4", "-vf",  "scale=in_range=limited:out_range=full",  "-f",  "rawvideo", "-pix_fmt", "yuv420p", f"1_renderedScene/texture/v{CamIdx:02d}_texture_{width}x{height}_yuv420p.yuv"]
    print(FFMPEG_Args)
    subprocess.call(FFMPEG_Args, shell=True)
    
  return

if __name__ == '__main__':
    main()


