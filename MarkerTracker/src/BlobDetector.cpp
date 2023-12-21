#include "BlobDetector.h"

void BlobDetector::init(const Mat& _mask)
{
    assert(_mask.empty() == false);

    vector<Mat> masks_components{ 3 };
    split(_mask, masks_components);
    // split components
    masks_components[0].copyTo(m_Ymask);
    masks_components[1].copyTo(m_Umask);
    masks_components[2].copyTo(m_Vmask);

    //equalizeHist(m_Ymask, m_Ymask);
    //equalizeHist(m_Umask, m_Umask);
    //equalizeHist(m_Vmask, m_Vmask);
    
    GaussianBlur(m_Ymask, m_Ymask, Size(3, 3), 0);
    GaussianBlur(m_Umask, m_Umask, Size(3, 3), 0);
    GaussianBlur(m_Vmask, m_Vmask, Size(3, 3), 0);
    
    // 1. preserve pixels above min thresh
    threshold(m_Ymask, m_Ymask, m_Y.m_min, 255, ThresholdTypes::THRESH_TOZERO);
    threshold(m_Umask, m_Umask, m_U.m_min, 255, ThresholdTypes::THRESH_TOZERO); 
    threshold(m_Vmask, m_Vmask, m_V.m_min, 255, ThresholdTypes::THRESH_TOZERO);

    // 2. preserve pixels below max thresh
    threshold(m_Ymask, m_Ymask, m_Y.m_max, 255, ThresholdTypes::THRESH_TOZERO_INV);
    threshold(m_Umask, m_Umask, m_U.m_max, 255, ThresholdTypes::THRESH_TOZERO_INV);
    threshold(m_Vmask, m_Vmask, m_V.m_max, 255, ThresholdTypes::THRESH_TOZERO_INV);     
    
    // 3. binarize preserved pixels
    threshold(m_Ymask, m_Ymask, 0, 255, ThresholdTypes::THRESH_BINARY);
    threshold(m_Umask, m_Umask, 0, 255, ThresholdTypes::THRESH_BINARY);
    threshold(m_Vmask, m_Vmask, 0, 255, ThresholdTypes::THRESH_BINARY);
    
    // 4. remove small blobs
    erode(m_Ymask, m_Ymask, m_erodeKernel);
    erode(m_Umask, m_Umask, m_erodeKernel);
    erode(m_Vmask, m_Vmask, m_erodeKernel);

    // 5. dilate remaining blobs
    dilate(m_Ymask, m_Ymask, m_dilateKernel);
    dilate(m_Umask, m_Umask, m_dilateKernel);
    dilate(m_Vmask, m_Vmask, m_dilateKernel); 



    

    bitwise_not(m_Ymask, m_YmaskInv);
    bitwise_not(m_Umask, m_UmaskInv);
    bitwise_not(m_Vmask, m_VmaskInv);

    
    
    Rect bound(10, 10, _mask.size().width - 20, _mask.size().height - 20);
    Mat maskBound = 255 * Mat::ones(_mask.size(), CV_8UC1);

    rectangle(maskBound, bound, Scalar(0), -1);

    bitwise_or(maskBound, m_Ymask, m_Ymask);
    bitwise_or(maskBound, m_Umask, m_Umask);
    bitwise_or(maskBound, m_Vmask, m_Vmask);  

    
    //imshow("mask", mask); cv::waitKey(0);
    // aggregate masks
    bitwise_or(m_Ymask, m_Umask, m_Umask);
    bitwise_or(m_Umask, m_Vmask, m_mask_aggregated);  
    //imshow("first thresh mask", m_VmaskInv); //waitKey();
    //imshow("dupa", m_mask_aggregated); waitKey();
}

void BlobDetector::apply(const Mat& _image, const Rect& _window)
{
    
    assert(_image.empty() == false);
    assert(_image.type() == CV_8UC3);
    
    m_window = _window;
    // window cut
    m_rawImage = Mat::zeros(_image.size(), CV_8UC3);
    _image.copyTo(m_rawImage, m_diffMask);
    
    //imshow("masked", m_rawImage);
    m_rawImage = m_rawImage(m_window);
    //m_rawImage = _image;
    
    //imshow("masked", _image); waitKey(0);

   

    m_YmaskInvWindow = m_YmaskInv(m_window); 
    m_UmaskInvWindow = m_UmaskInv(m_window); 
    m_VmaskInvWindow = m_VmaskInv(m_window);  


    m_YmaskWindow = m_Ymask(m_window);
    m_UmaskWindow = m_Umask(m_window);
    m_VmaskWindow = m_Vmask(m_window);

    //erode(m_YmaskInvWindow, m_YmaskInvWindow, getStructuringElement(MorphShapes::MORPH_ELLIPSE, Size(7,7)));
    //erode(m_UmaskInvWindow, m_UmaskInvWindow, getStructuringElement(MorphShapes::MORPH_ELLIPSE, Size(7,7)));
    //erode(m_VmaskInvWindow, m_VmaskInvWindow, getStructuringElement(MorphShapes::MORPH_ELLIPSE, Size(7,7)));
    //imshow("mask inv", m_UmaskInvWindow);

    // cut component
    vector<Mat> image_components{ 3 };
    split(m_rawImage, image_components);
    image_components[0].copyTo(m_Ycomp_src, m_YmaskInvWindow);
    image_components[1].copyTo(m_Ucomp_src, m_UmaskInvWindow);
    image_components[2].copyTo(m_Vcomp_src, m_VmaskInvWindow);
    
    
    //cvtColor(image, gray, COLOR_BGR2GRAY); ???
    
    //equalizeHist(m_Ycomp_src, m_Ycomp_src);
    //equalizeHist(m_Ucomp_src, m_Ucomp_src);
    //equalizeHist(m_Vcomp_src, m_Vcomp_src);
    //imshow("equalized", m_Ucomp_src); waitKey();

    // blur
    GaussianBlur(m_Ycomp_src, m_Ygray, Size(3, 3), 0);
    GaussianBlur(m_Ucomp_src, m_Ugray, Size(3, 3), 0);
    GaussianBlur(m_Vcomp_src, m_Vgray, Size(3, 3), 0); 

    // 1. preserve pixels above min thresh
    threshold(m_Ycomp_src, m_Ybinary, m_Y.m_min, 255, THRESH_TOZERO); 
    threshold(m_Ucomp_src, m_Ubinary, m_U.m_min, 255, THRESH_TOZERO); 
    threshold(m_Vcomp_src, m_Vbinary, m_V.m_min, 255, THRESH_TOZERO);

    // 2. preserve pixels below max thresh
    threshold(m_Ybinary, m_Ybinary, m_Y.m_max, 255, THRESH_TOZERO_INV);
    threshold(m_Ubinary, m_Ubinary, m_U.m_max, 255, THRESH_TOZERO_INV);   //imshow("second thresh", m_Ubinary);
    threshold(m_Vbinary, m_Vbinary, m_V.m_max, 255, THRESH_TOZERO_INV); 
    
    // 3. binarize preserved pixels
    threshold(m_Ybinary, m_Ybinary, 0, 255, ThresholdTypes::THRESH_BINARY);
    threshold(m_Ubinary, m_Ubinary, 0, 255, ThresholdTypes::THRESH_BINARY); //imshow("first thresh mask", m_Umask);
    threshold(m_Vbinary, m_Vbinary, 0, 255, ThresholdTypes::THRESH_BINARY);
  
    // 4. remove small blobs
    erode(m_Ybinary, m_Ybinary, getStructuringElement(MorphShapes::MORPH_ELLIPSE, Size(11, 11)));
    erode(m_Ubinary, m_Ubinary, getStructuringElement(MorphShapes::MORPH_ELLIPSE, Size(11, 11)));
    erode(m_Vbinary, m_Vbinary, getStructuringElement(MorphShapes::MORPH_ELLIPSE, Size(11, 11)));

    // 5. dilate remaining blobs
    dilate(m_Ybinary, m_Ybinary, getStructuringElement(MorphShapes::MORPH_ELLIPSE, Size(3, 3)));
    dilate(m_Ubinary, m_Ubinary, getStructuringElement(MorphShapes::MORPH_ELLIPSE, Size(3, 3)));
    dilate(m_Vbinary, m_Vbinary, getStructuringElement(MorphShapes::MORPH_ELLIPSE, Size(3, 3)));
    

    

    // aggregate binary images
    bitwise_or(m_Ybinary, m_Ubinary, m_Ubinary);
    bitwise_or(m_Ubinary, m_Vbinary, m_binary_aggregated); 

    Canny(m_binary_aggregated, m_edges_aggregated, 0, 255);
    m_contours_aggregated.clear();
    findContours(m_edges_aggregated, m_contours_aggregated, RetrievalModes::RETR_EXTERNAL, ContourApproximationModes::CHAIN_APPROX_SIMPLE);

    //imshow("edges", m_edges_aggregated); //waitKey();
    m_blobs.clear();
    uint8_t ID = 0;
    for (const auto& contour : m_contours_aggregated)
    {
        Blob blob(contour, m_rawImage, m_binary_aggregated, ID++);
        m_blobs.push_back(blob);
    }

    filterBlobs();
    
    //waitKey();
}

Blob BlobDetector::getBestBlob(const Rect2d& window)
{
    vector<Blob> best;
    //w calej ramce nic nie znaleziono
   

    for (auto blob : m_filteredBlobs)
    {
        for (auto pt : blob.getContour())
            if (window.contains(pt)) 
            {
                best.push_back(blob);
                break;
            }
    }
    m_filteredBlobs.clear();
    m_filteredBlobs = best;
    if(m_filteredBlobs.empty())
            return Blob(Point2d(-1, -1));

    sortBlobs();
    //if (m_sortedByIntensivity.front().getID() == m_sortedByCircularity.front().getID())
    if (m_sortedByArea.front().getID() == m_sortedByCircularity.front().getID() && m_sortedByArea.front().getID() == m_sortedByIntensivity.front().getID())
        return m_sortedByArea.front();
    else 
        return Blob(Point2d(-1, -1));

}

void BlobDetector::filterBlobs()
{

    m_filteredBlobs.clear();

    //filter by mask overlap
    for (const auto& blob : m_blobs)
    {
        if (blob.isOnMask(m_mask_aggregated))continue;
        //if (blob.getCircularity() < 0.75) continue;
        if (blob.getArea() < 2 * 2) continue;
       
            
        m_filteredBlobs.push_back(blob);
    }

}

void BlobDetector::sortBlobs()
{
    auto sortByIntensivity = [&](const Blob& a, const Blob& b) -> bool
    {
        return a.getIntensity() > b.getIntensity();
    };

    auto sortByCircularity = [&](const Blob& a, const Blob& b) -> bool
    {
        return a.getCircularity() < b.getCircularity();
    };

    auto sortByArea = [&](const Blob& a, const Blob& b) -> bool
    {
        return a.getArea() > b.getArea();
    };

    m_sortedByIntensivity = m_filteredBlobs;
    sort(m_sortedByIntensivity.begin(), m_sortedByIntensivity.end(), sortByIntensivity);

    m_sortedByCircularity = m_filteredBlobs;
    sort(m_sortedByCircularity.begin(), m_sortedByCircularity.end(), sortByCircularity);

    m_sortedByArea = m_filteredBlobs;
    sort(m_sortedByArea.begin(), m_sortedByArea.end(), sortByArea);
    
}

void BlobDetector::diffMask(const Mat& prevFrame, const Mat& currFrame)
{

    prevFrame.copyTo(m_prevFrame);
    currFrame.copyTo(m_currFrame);

    Mat prevGray, currGray;

    cvtColor(m_prevFrame, m_prevFrame, COLOR_YUV2BGR);
    cvtColor(m_prevFrame, prevGray, COLOR_BGR2GRAY);
    cvtColor(m_currFrame, m_currFrame, COLOR_YUV2BGR);
    cvtColor(m_currFrame, currGray, COLOR_BGR2GRAY);

    Mat flow(prevFrame.size(), CV_32FC2);
    //calcOpticalFlowFarneback(prevGray, currGray, flow, 0.5, 3, 15, 3, 5, 1.2, 0);
    //// visualization
    //Mat flow_parts[2];
    //split(flow, flow_parts);
    //Mat magnitude, angle, magn_norm;
    //cartToPolar(flow_parts[0], flow_parts[1], magnitude, angle, true);
    //normalize(magnitude, magn_norm, 0.0f, 1.0f, NORM_MINMAX);
    //angle *= ((1.f / 360.f) * (180.f / 255.f));
    ////build hsv image
    //Mat _hsv[3], hsv, hsv8, bgr;
    //_hsv[0] = angle;
    //_hsv[1] = Mat::ones(angle.size(), CV_32F);
    //_hsv[2] = magn_norm;
    //merge(_hsv, 3, hsv);
    //hsv.convertTo(hsv8, CV_8U, 255.0);
    //cvtColor(hsv8, bgr, COLOR_HSV2BGR);
    //cvtColor(bgr, bgr, COLOR_BGR2GRAY);
    //threshold(bgr, bgr, 50, 255, THRESH_BINARY);
    //imshow("optflow", bgr); //waitKey();
    //

    Mat diffFrame = currFrame - prevFrame;
    cvtColor(diffFrame, diffFrame, COLOR_BGR2GRAY);
    threshold(diffFrame, diffFrame, 10, 255, THRESH_BINARY);


    erode(diffFrame, diffFrame, getStructuringElement(MorphShapes::MORPH_ELLIPSE, Size{ 3,3 }));
    dilate(diffFrame, diffFrame, getStructuringElement(MorphShapes::MORPH_ELLIPSE, Size{ 11,11}));

    //bitwise_not(diffFrame, diffFrame);


    vector<vector<Point>> contours;
    Mat edges;
    Canny(diffFrame, edges, 0, 255);
    findContours(edges, contours, RetrievalModes::RETR_EXTERNAL, ContourApproximationModes::CHAIN_APPROX_NONE);

    vector<Blob> diffBlobs;

    //for (auto contour : contours) {
    //    //Blob blob{contour,}
    //}


    //imshow("diff", diffFrame); //waitKey();


    diffFrame.copyTo(m_diffMask);
}