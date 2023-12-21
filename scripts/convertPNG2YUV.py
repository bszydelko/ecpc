import os
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
    for OrgIdx in range(start_frame, end_frame+1, step_frame):
      NewIdx = OrgIdx // step_frame
      org = f"1_renderedScene/depth/depth{OrgIdx:04d}.{CamIdx:03d}.png"
      new = f"1_renderedScene/depth/depth{NewIdx:04d}.{CamIdx:03d}.png"
      print(org, new)
      os.rename(org, new)

  for CamIdx in range(0, num_of_cams):
    FFMPEG_Args = ['ffmpeg', "-pattern_type", "sequence", "-i", f"1_renderedScene/depth/depth%04d.{CamIdx:03d}.png", "-vf",  "scale=in_range=limited:out_range=full",  "-f",  "rawvideo", "-pix_fmt", "yuv420p16le", f"1_renderedScene/depth/v{CamIdx:02d}_depth_{width}x{height}_yuv420p16le.yuv"]
    #print(FFMPEG_Args)
    subprocess.call(FFMPEG_Args, shell=True)
    
  return

if __name__ == '__main__':
  main()