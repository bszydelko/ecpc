#pragma once
#include <opencv2/opencv.hpp>
#include "Blob.h"

using namespace cv;
using namespace std;

struct thresh {
	uint8_t m_min;
	uint8_t m_max;
	bool use;

	thresh() : m_min{ std::numeric_limits<uint8_t>::max()}, m_max{ std::numeric_limits<uint8_t>::max() } { use = false; } //set max for min max
	thresh(const uint8_t min, const uint8_t max) : m_min{ min }, m_max{ max } { use = true; }
	
};

class BlobDetector
{
public:
	BlobDetector(const thresh& Y, const thresh& U, const thresh& V) 
		: m_Y{ Y }, m_U{ U }, m_V{ V } {
		;
	}
	void init(const Mat& _mask);
	void apply(const Mat& _image, const Rect& _window);

	Blob getBestBlob(const Rect2d& window);

	void diffMask(const Mat& prevFrame, const Mat& currFrame);

private:
	Rect m_window;

	Mat m_rawImage;
	Mat m_image;

	// windows for masks
	Mat m_YmaskInvWindow;
	Mat m_UmaskInvWindow;
	Mat m_VmaskInvWindow;

	Mat m_YmaskWindow;
	Mat m_UmaskWindow;
	Mat m_VmaskWindow;

	// mask for each component
	Mat m_Ymask;
	Mat m_Umask;
	Mat m_Vmask;

	Mat m_YmaskInv;
	Mat m_UmaskInv;
	Mat m_VmaskInv;

	Mat m_mask_aggregated;

	// gray images for each component
	Mat m_Ygray;
	Mat m_Ugray;
	Mat m_Vgray;

	// binary image for each component after thresholding
	Mat m_Ybinary;
	Mat m_Ubinary;
	Mat m_Vbinary;

	Mat m_binary_aggregated;

	// edges of blobs from binary images for each component
	Mat m_Yedges;
	Mat m_Uedges;
	Mat m_Vedges;

	Mat m_edges_aggregated;

	// components
	Mat m_Ycomp_src;
	Mat m_Ucomp_src;
	Mat m_Vcomp_src;

	// thresholds (min, max) for each component
	thresh m_Y;
	thresh m_U;
	thresh m_V;

	// component contorus
	vector<vector<Point>> m_Ycontours;
	vector<vector<Point>> m_Ucontours;
	vector<vector<Point>> m_Vcontours;
	vector<vector<Point>> m_contours_aggregated;


	Mat m_dilateKernel{ getStructuringElement(MorphShapes::MORPH_ELLIPSE, Size(3,3)) };
	Mat m_erodeKernel { getStructuringElement(MorphShapes::MORPH_ELLIPSE, Size(3,3)) };


	vector<Blob> m_blobs;
	vector<Blob> m_filteredBlobs;
	vector<Blob> m_sortedByIntensivity;
	vector<Blob> m_sortedByCircularity;
	vector<Blob> m_sortedByArea;

	vector<Blob> m_history;

	uint32_t m_avgArea{ 0 };

	Mat m_prevFrame;
	Mat m_currFrame;
	Mat m_diffMask;

	void filterBlobs();
	void sortBlobs();

};

