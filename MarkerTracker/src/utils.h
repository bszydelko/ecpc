#pragma once
#include <opencv2/opencv.hpp>
#include "Blob.h"

using namespace std;
using namespace cv;

void drawCircles(Mat& frame, const vector<Point2d>& locs, int history)
{
	int h = 0;
	int colourJmp = 255 / history;
	int RED = 255;

	for (size_t i = locs.size() - 1; i >= 0; i--)
	{
		if (h == history) break;

		circle(frame, Point2d(locs[i]), 15, Scalar(0, 0, RED), 3);

		RED -= colourJmp;
		if (RED <= 0) RED = 1;
		h++;
	}

}
void drawLines(Mat& frame, const vector<Blob>& blobs, int history)
{
	int h = 0;

	Point2d pt1 = blobs[blobs.size() - 1].getCentroid();
	Point2d pt2(-1, -1);

	if (blobs.size() < 2) return;
	for (size_t i = blobs.size() - 2; i > 0; i--)
	{
		if (h == history) break;

		if (pt1 != Point2d(-1, -1))
		{
			pt2 = blobs[i].getCentroid();
			if (pt2 != Point2d(-1, -1)) {
				line(frame, pt1, pt2, Scalar(0, 255, 0), 2);
				pt1 = pt2;
			}
		}
		h++;
	}
}

void drawLines(Mat& frame, const vector<Point>& pts, int history)
{
	int h = 0;

	Point2d pt1 = pts[pts.size() - 1];
	Point2d pt2(-1, -1);

	if (pts.size() < 2) return;
	for (size_t i = pts.size() - 2; i > 0; i--)
	{
		if (h == history) break;

		if (pt1 != Point2d(-1, -1))
		{
			pt2 = pts[i];
			if (pt2 != Point2d(-1, -1)) {
				line(frame, pt1, pt2, Scalar(0, 255, 255), 2);
				pt1 = pt2;
			}
		}
		h++;
	}
}

void drawInfo(Mat& frame, int seqNum, int frameNum, const Point2d& detected, const Point& predicted)
{
	int font = HersheyFonts::FONT_HERSHEY_SIMPLEX;

	//frame num, seq num
	putText(frame, "cam: " + to_string(seqNum), Point(1,30), font,1, Scalar(0, 0, 0), 3);
	putText(frame, "cam: " + to_string(seqNum), Point(1,30), font,1, Scalar(255, 255, 255), 1);

	putText(frame, "frame: " + to_string(frameNum), Point(1, 60), font, 1, Scalar(0, 0, 0),3);
	putText(frame, "frame: " + to_string(frameNum), Point(1, 60), font, 1, Scalar(255, 255, 255), 1);
	//detected
	putText(frame, "x: " + to_string(detected.x), Point(1, 100), font, 1, Scalar(0, 128, 0), 3);
	putText(frame, "x: " + to_string(detected.x), Point(1, 100), font, 1, Scalar(0, 255, 0), 1);

	putText(frame, "y: " + to_string(detected.y), Point(1, 130), font, 1, Scalar(0, 128, 0), 3);
	putText(frame, "y: " + to_string(detected.y), Point(1, 130), font, 1, Scalar(0, 255, 0), 1);
	//predicted 
	putText(frame, "x: " + to_string(predicted.x), Point(1, 170), font, 1, Scalar(0, 128, 128), 3);
	putText(frame, "x: " + to_string(predicted.x), Point(1, 170), font, 1, Scalar(0, 255, 255), 1);

	putText(frame, "y: " + to_string(predicted.y), Point(1, 200), font, 1, Scalar(0, 128, 128), 3);
	putText(frame, "y: " + to_string(predicted.y), Point(1, 200), font, 1, Scalar(0, 255,255), 1);



}
