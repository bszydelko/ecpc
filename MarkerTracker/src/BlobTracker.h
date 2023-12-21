#pragma once
#include <opencv2/opencv.hpp>
#include <iostream>
#include <vector>

using namespace std;
using namespace cv;

class BlobTracker
{
public:
	BlobTracker() {};

	void init(const vector<Point2d>& _initPos, const Size& _seqResolution);
	
	Point predict();
	Rect2d window(int sizeFactor);
	
	void update(const Point2d& _pos);

private:
	Size            seqResolution;
	Point2d         predicted;
	vector<Point2d> detectedPositions;
	vector<Point2d> allPositions;

	

	double avgDist(int n);
	double distance(const Point& pt1, const Point& pt2);


};

