#pragma once
#include <opencv2/opencv.hpp>

using namespace std;
using namespace cv;

class Blob
{
private:
	uint8_t ID;

	Mat mask;
	Mat image;
	vector<Point> contour;
	Moments cntMoments;

	Scalar intensityRGB;
	uint32_t intensitySum;

	double circularity;
	double perimeter;
	double area;

	Point2d centroid;

	bool convex;
	bool correct;

	Rect2d rect;

public:
	Blob();
	Blob(Point2d _centroid)	{	centroid = _centroid;	}
	Blob(const vector<Point>& _contour, const Mat& _image, const Mat& _mask, uint8_t _ID);

	uint32_t getIntensity() const { return intensitySum; }
	double   getCircularity() const { return circularity; }
	double   getArea() const { return area; }
	Point2d  getCentroid() const { return Point2d(centroid); }
	vector<Point> getContour() const { return vector<Point>(contour); }

	double getEquivalentDiameter() const { return sqrt(4 * area / CV_PI); }

	bool isConvex() const { return convex; }
	bool isOnMask(const Mat& mask) const;
	bool isCorrect() const { return correct; }

	uint8_t getID() { return uint8_t(ID); }

	void includeWindowOffset(const Rect& window);

};

