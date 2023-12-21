#include "Blob.h"

Blob::Blob()
{
	contour.clear();
	intensitySum = 0;
	circularity = 0.0;
	perimeter = 0.0;
	area = 0.0;
	centroid = Point2d(-1, -1);
	convex = false;
	correct = false;
}
Blob::Blob(const vector<Point>& _contour, const Mat& _image, const Mat& _mask, uint8_t _ID)
{
	ID = _ID;
	contour = _contour;
	cntMoments = moments(contour);

	if (cntMoments.m00 != 0)
	{
		centroid = Point2d((cntMoments.m10 / cntMoments.m00), (cntMoments.m01 / cntMoments.m00));

		rect = boundingRect(contour);

		image = _image(rect);
		mask = _mask(rect);

		intensityRGB = mean(image, mask);
		intensitySum = intensityRGB[0] + intensityRGB[1] + intensityRGB[2];

		area = contourArea(contour);
		perimeter = arcLength(contour, true);
		circularity = 4 * CV_PI * area / (perimeter * perimeter);

		convex = isContourConvex(contour);
	}
	else 
	{
		centroid = Point2d(-1, -1);
		intensityRGB = { 0,0,0,0 };
		area = 0;
		perimeter = 0;
		circularity = 0;
		convex = false;

	}
}
bool Blob::isOnMask(const Mat& mask) const
{
	for (const auto& point : contour)
	{
		if (mask.at<uint8_t>(point)) return true;
	}

	return false;
}
void Blob::includeWindowOffset(const Rect& window)
{
	centroid.x += window.tl().x;
	centroid.y += window.tl().y;
}


