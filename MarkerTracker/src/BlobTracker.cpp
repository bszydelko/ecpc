#include "BlobTracker.h"

void BlobTracker::init(const vector<Point2d>& _initPos, const Size& _seqResolution)
{
  seqResolution = _seqResolution;

  for(auto p : _initPos)
  {
    if(p != Point2d(-1, -1)) { detectedPositions.push_back(p); }

    allPositions.push_back(p);
  }

}

Point BlobTracker::predict()
{
  Point predictedPosition;        // this will be the return value
  int   numPositions;

  numPositions = detectedPositions.size();

  if(numPositions == 0)
  {
    cout << "error, predictNextPosition was called with zero points\n";
  }
  else if(numPositions == 1)
  {
    return(detectedPositions[0]);
  }
  else if(numPositions == 2)
  {
    int deltaX = detectedPositions[1].x - detectedPositions[0].x;
    int deltaY = detectedPositions[1].y - detectedPositions[0].y;

    predictedPosition.x = detectedPositions.back().x + deltaX;
    predictedPosition.y = detectedPositions.back().y + deltaY;
  }
  else if(numPositions == 3)
  {
    int sumOfXChanges = ((detectedPositions[2].x - detectedPositions[1].x) * 2) + ((detectedPositions[1].x - detectedPositions[0].x) * 1);

    int deltaX = (int)std::round((float)sumOfXChanges / 3.0);

    int sumOfYChanges = ((detectedPositions[2].y - detectedPositions[1].y) * 2) + ((detectedPositions[1].y - detectedPositions[0].y) * 1);

    int deltaY = (int)std::round((float)sumOfYChanges / 3.0);

    predictedPosition.x = detectedPositions.back().x + deltaX;
    predictedPosition.y = detectedPositions.back().y + deltaY;
  }
  else if(numPositions == 4) 
  {
    int sumOfXChanges = ((detectedPositions[3].x - detectedPositions[2].x) * 3) + ((detectedPositions[2].x - detectedPositions[1].x) * 2) + ((detectedPositions[1].x - detectedPositions[0].x) * 1);

    int deltaX = (int)std::round((float)sumOfXChanges / 6.0);

    int sumOfYChanges = ((detectedPositions[3].y - detectedPositions[2].y) * 3) + ((detectedPositions[2].y - detectedPositions[1].y) * 2) + ((detectedPositions[1].y - detectedPositions[0].y) * 1);

    int deltaY = (int)std::round((float)sumOfYChanges / 6.0);

    predictedPosition.x = detectedPositions.back().x + deltaX;
    predictedPosition.y = detectedPositions.back().y + deltaY;
  }
  else if(numPositions >= 5) 
  {
    int sumOfXChanges = ((detectedPositions[numPositions - 1].x - detectedPositions[numPositions - 2].x) * 4) +
      ((detectedPositions[numPositions - 2].x - detectedPositions[numPositions - 3].x) * 3) +
      ((detectedPositions[numPositions - 3].x - detectedPositions[numPositions - 4].x) * 2) +
      ((detectedPositions[numPositions - 4].x - detectedPositions[numPositions - 5].x) * 1);

    int deltaX = (int)std::round((float)sumOfXChanges / 10.0);

    int sumOfYChanges = ((detectedPositions[numPositions - 1].y - detectedPositions[numPositions - 2].y) * 4) +
      ((detectedPositions[numPositions - 2].y - detectedPositions[numPositions - 3].y) * 3) +
      ((detectedPositions[numPositions - 3].y - detectedPositions[numPositions - 4].y) * 2) +
      ((detectedPositions[numPositions - 4].y - detectedPositions[numPositions - 5].y) * 1);

    int deltaY = (int)std::round((float)sumOfYChanges / 10.0);

    predictedPosition.x = detectedPositions.back().x + deltaX;
    predictedPosition.y = detectedPositions.back().y + deltaY;
  }
  else
  {
    // should never get here
    assert(0);
  }

  predicted = predictedPosition;
  return(predictedPosition);
}

Rect2d BlobTracker::window(int sizeFactor = 1)
{
  //double size = avgDist(4) * sizeFactor;
  double size = avgDist(4) * sizeFactor;

  if(size <= 0) size = seqResolution.width;

  cv::Rect2d _window(predicted.x - size / 2.0, predicted.y - size / 2.0, size, size);

  if(_window.width > seqResolution.width  ) { _window.width  = seqResolution.width; }
  if(_window.height > seqResolution.height) { _window.height = seqResolution.height; }

  double minSize = 100;
  if(_window.width < minSize || _window.height < minSize)
  {
    _window.width = minSize;
    _window.height = minSize;
    _window.x = predicted.x - minSize / 2.0;
    _window.y = predicted.y - minSize / 2.0;
  }

  if(_window.x < 0                                    ) { _window.x = 0; }
  if(_window.x + _window.width > seqResolution.width  ) { _window.x = seqResolution.width - _window.width; }
  if(_window.y < 0                                    ) { _window.y = 0; }
  if(_window.y + _window.height > seqResolution.height) { _window.y = seqResolution.height - _window.height; }

  return cv::Rect2d(_window);
}
void BlobTracker::update(const Point2d& _pos)
{
  allPositions.push_back(_pos);
  if(_pos != predicted) { detectedPositions.push_back(_pos); }
}
double BlobTracker::avgDist(int n)
{
  double sum = 0.0;
  if(n > detectedPositions.size()) n = detectedPositions.size();
  if(n == 1) sum = std::sqrt(
    std::pow(detectedPositions.back().x, 2) +
    std::pow(detectedPositions.back().y, 2));
  else sum = std::sqrt(
    std::pow(detectedPositions.back().x - predicted.x, 2) +
    std::pow(detectedPositions.back().y - predicted.y, 2));
  auto it = detectedPositions.rbegin();

  for(int i = 0; i < n - 1; i++)
  {
    sum += (std::sqrt(std::pow((*it).x - (*(it + 1)).x, 2) + std::pow((*it).y - (*(it + 1)).y, 2)));

    ++it;
  }
  return sum / (double)n;
}
double BlobTracker::distance(const Point& pt1, const Point& pt2)
{
  double a_2 = pow(pt1.x - pt2.x, 2);
  double b_2 = pow(pt1.y - pt2.y, 2);

  double c = sqrt(a_2 + b_2);

  return c;
}
