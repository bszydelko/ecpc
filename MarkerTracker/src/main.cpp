#pragma once
#include <opencv2/opencv.hpp>
#include <opencv2/imgproc.hpp>
#include "CaptureYUV.h"
#include <chrono>
#include <vector>
#include <filesystem>
#include "BlobDetector.h"
#include "BlobTracker.h"
#include "FileManager.h"
#include "utils.h"

using namespace bs;

struct Params {
	int nseq;
	int nframes;
	string seqlist;
	string masklist;
	string output;
	int seqwidth;
	int seqheight;
	int chroma;
	int bps;

	void help()
  {
		cout << "Usage: \n";
		cout << "\t --nseq <number of sequences>\n";
		cout << "\t --nframes <number of frames>\n";
		cout << "\t --seq <sequence path list>\n";
		cout << "\t --mask <mask path list>\n";
		cout << "\t --w <width>\n";
		cout << "\t --h <height>\n";
		cout << "\t --cs <chroma>\n";
		cout << "\t --out <output points filename>\n";
		cout << "NOTE: sequences and masks are only 420p8le yuvs\n";
	}
};

void parseArgs(int argc, char** const argv, Params& params)
{
	if (argc - 1 != 16) {
		params.help();
		exit(EXIT_FAILURE);
	}

	vector<string> args;
	for (int i = 1; i < argc; i++)
		args.push_back(argv[i]);

	for (auto it = args.begin(); it != args.end(); it++) 
  {
		string token = *it;
		
		if      (token == "--nseq"   ) { it++; params.nseq      = stoi(*it); }
		else if (token == "--nframes") { it++; params.nframes   = stoi(*it); }
		else if (token == "--seq"    ) { it++; params.seqlist   = *it;       }
		else if (token == "--mask"   ) { it++; params.masklist  = *it;       }
		else if (token == "--w"      ) { it++; params.seqwidth  = stoi(*it); }	
		else if (token == "--h"      ) { it++; params.seqheight = stoi(*it); }
		else if (token == "--cs"     ) { it++; params.chroma    = stoi(*it); }
    else if (token == "--out"    ) { it++; params.output    = *it;       }
		else    {cout << "Bad argument" << endl; exit(EXIT_FAILURE);         }
	}
}

int main(int argc, char** argv)
{
	cout << "WorkingDir = " << std::filesystem::current_path().string() <<"\n";

	Params params;
	cout << "Reading params...";
	parseArgs(argc, argv, params);
	cout << "done\n";
		
	int    seqCount     = params.nseq;
	int    frameCount   = params.nframes;
	String seqListPath  = params.seqlist;
	String maskListPath = params.masklist;
	int    width        = params.seqwidth;
	int    height       = params.seqheight;
	int    chromaSubsampling = params.chroma;
	int    bps          = params.bps;
	String outputFile   = params.output;
	
	cout << "Reading files...";
	FileManager fileManager(seqListPath, maskListPath);
	cout << "done\n";

	Size seqResolution(width, height);
	
	Mat prevFrame;
	Mat currFrame;
	Mat colorFrame;
	Mat mask;

	BlobDetector blobDetectorDetail{ {}, {50,70}, {155,195} }; 


	Blob bestBlob;
	vector<Blob> blobHistory;
	Rect2d detectWindow(Point(0, 0), seqResolution);

	BlobTracker blobTracker;
	vector<Point2d> initPts;
	vector<Point> predictedPts;
	Rect2d trackWindow;
	Rect2d diffWindow;
	int maxWindowScaler  = 3;
	int windowScaler = 1;
	int lastWindowScaler = 0;
	const cv::Point2d NOT_DETECTED(-1, -1);

	int key = 0;
	int waitTime = 1;
	
	uint8_t frameStep = 1;

	frameCount = frameStep * (frameCount / frameStep);

	cv::Point2d** points = new cv::Point2d * [frameCount/frameStep];
	for(size_t i = 0; i < frameCount / frameStep; i++) { points[i] = new cv::Point2d[seqCount]; }

	int seqNum = 0;
	int frameNum = 0;
	int initialFrames = std::min(5, params.nframes);



	auto start = chrono::high_resolution_clock::now();

	cout << "Tracking...\n";
	while (!fileManager.eof() && seqNum < seqCount)
	{
		string sequenceName = fileManager.getSequencePath();
		string maskName = fileManager.getMaskPath();

		CaptureYUV sequenceCap(sequenceName, width, height, chromaSubsampling, frameStep);
		CaptureYUV maskCap(maskName, width, height, chromaSubsampling, 1);
		CaptureYUV colorCap(sequenceName, width, height, chromaSubsampling, frameStep);

		maskCap.read(mask);
		
		blobDetectorDetail.init(mask);
		blobHistory.clear();

		detectWindow = Rect2d(Point(0, 0), seqResolution);

		cout << "SequenceName = " << sequenceName << endl;
		cout << "MaskName     = " << maskName << endl;

		//initial frames
		initPts.clear();
		frameNum = 0;

		colorCap.read(colorFrame);
		sequenceCap.read(currFrame);
		currFrame.copyTo(prevFrame);

		for (size_t i = 1; i < initialFrames; i++, frameNum++)
		{
			sequenceCap.read(currFrame);
	
			
			colorCap.read(colorFrame);
			
			blobDetectorDetail.diffMask(prevFrame, currFrame);
			blobDetectorDetail.apply(currFrame, detectWindow);
			bestBlob = blobDetectorDetail.getBestBlob(detectWindow);
			initPts.push_back(bestBlob.getCentroid());
			blobHistory.push_back(bestBlob.getCentroid());

			currFrame.copyTo(prevFrame);
			
		}
		predictedPts.clear();
		blobTracker.init(initPts, seqResolution);


		
		while (sequenceCap.read(currFrame) && frameNum < frameCount)
		{
			

			Point predictedPt = blobTracker.predict();
			//diffWindow = blobTracker.window(prevFrame, currFrame);
			//blobTracker.window(prevFrame, currFrame);

			do
			{
				blobDetectorDetail.diffMask(prevFrame, currFrame);
				blobDetectorDetail.apply(currFrame, detectWindow);
			
				if (lastWindowScaler <= maxWindowScaler) {
					trackWindow = blobTracker.window(windowScaler);
				}
				else {
					trackWindow = detectWindow;
				}

				bestBlob = blobDetectorDetail.getBestBlob(trackWindow);

				windowScaler++;

			} while (windowScaler <= maxWindowScaler && bestBlob.getCentroid() == NOT_DETECTED);

			lastWindowScaler = windowScaler;
			windowScaler = 1;

			if (bestBlob.getCentroid() == NOT_DETECTED) {
				//bestBlob = blobDetectorDetail.getBestBlob(diffWindow);
			}

			if (bestBlob.getCentroid() != NOT_DETECTED)
				blobTracker.update(bestBlob.getCentroid());
			else
				blobTracker.update(predictedPt);

			predictedPts.push_back(predictedPt);
			blobHistory.push_back(bestBlob);


			colorCap.read(colorFrame);
			cvtColor(colorFrame, colorFrame, COLOR_YUV2BGR);
			drawLines(colorFrame, blobHistory, 800);
			drawLines(colorFrame, predictedPts, 800);

			circle(colorFrame, predictedPt, 10, Scalar(0, 255, 255), 2);
			circle(colorFrame, bestBlob.getCentroid(), 10, Scalar(0, 255, 0), 2);

			rectangle(colorFrame, trackWindow, Scalar(255, 0, 0), 2);

			drawInfo(colorFrame, seqNum, frameNum, bestBlob.getCentroid(),predictedPt);
			std::cout << "Cam: " << seqNum << ", frame: " << frameNum << std::endl;
			imshow("frame", colorFrame);
			//writer.write(colorFrame);

			key = waitKey(waitTime);
			if (key == 27) break;
			if (key == 'n') break;
			
			if (key == 32) {
				waitTime = 0;
				
				if (waitKey(waitTime) == 'f') {
					waitTime = 0;
				}
				else {
					waitTime = 1;
				}
			}
			frameNum++;
			currFrame.copyTo(prevFrame);

		}
		
		if (key != 'n' && key != 27) {
			for (size_t i = 0; i < frameCount; i++)
			{
				points[i][seqNum] = blobHistory[i].getCentroid();
			}
		}
		seqNum++;

		if (key == 27) break;
	}

	auto finish = chrono::high_resolution_clock::now();
	std::chrono::duration<double> elapsed = finish - start;
	

	
	//--------------------------------------------------------------------------------------------
	//save to file - txt
	cout << "Writing results to " << outputFile << "\n";
	std::ofstream file_final_pos(outputFile, std::ios::out);

	for (size_t i = 0; i < frameCount/frameStep; i++)
	{
		for (size_t j = 0; j < seqNum; j++)
		{
			file_final_pos << std::setprecision(3) << std::fixed;
			if (points[i][j] == NOT_DETECTED)
				file_final_pos << points[i][j].x << "\t" << points[i][j].y << "\t" << 0;
			else
				file_final_pos << points[i][j].x << "\t" << points[i][j].y << "\t" << 1;
			
			if (j < seqNum - 1) file_final_pos << "\t";
		}
		
		file_final_pos << "\n";
	}
	file_final_pos.close();

	//--------------------------------------------------------------------------------------------
	//post mortem
	std::cout << "POINTS SAVED\n";
	std::cout << "Elapsed time: " << elapsed.count();	

	return EXIT_SUCCESS;
}