import subprocess
import shutil

def main():
    print("==== BUILD MarkerTracker ====\n")
    shutil.rmtree('./MarkerTracker/build', ignore_errors=True)
    subprocess.call(['cmake', '-S', './MarkerTracker', '-B', './MarkerTracker/build'], shell=True)
    subprocess.call(['cmake', '--build', './MarkerTracker/build', '--clean-first', '--config', 'Release', '--parallel'], shell=True)

    print("==== BUILD DepthEstimator/ivde ====\n")
    shutil.rmtree('./DepthEstimator/ivde/build', ignore_errors=True)
    subprocess.call(['cmake', '-S', './DepthEstimator/ivde', '-B', './DepthEstimator/ivde/build'], shell=True)
    subprocess.call(['cmake', '--build', './DepthEstimator/ivde/build', '--clean-first', '--config', 'Release', '--parallel'], shell=True)

if __name__ == '__main__':
    main()
