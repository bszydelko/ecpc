import numpy as np
import itertools
import math

try:
  import numba
  my_jit = numba.jit
except:
  def _noop_jit(f=None, *args, **kwargs):
    """ returns function unmodified, discarding decorator args"""
    if f is None: return lambda x: x
    return f
  my_jit = _noop_jit

#==============================================================================================================================================================
# CamUtils
#==============================================================================================================================================================
def calcAvgDistanceBetweenCameras(CameraIds, MainCamId, RelativeTranslationVs) -> float:
  TotalDistance = 0
  NumCams = len(CameraIds)
  for CamId in CameraIds:
    if CamId == MainCamId: continue
    PhysicalDistance = np.linalg.norm(RelativeTranslationVs[MainCamId] - RelativeTranslationVs[CamId])
    SystemDistance   = abs(CameraIds.index(MainCamId) - CameraIds.index(CamId))
    DistanceMetric   = PhysicalDistance/SystemDistance
    TotalDistance += DistanceMetric
  AverageDistance = TotalDistance/(NumCams-1)
  return AverageDistance

def calcMaxDistanceBetweenCameras(CameraIds, TranslationVs) -> float:
  if(len(CameraIds) == 0): return None
  if(len(CameraIds) == 1): return 0.0
  MaxPhysicalDistance = 0
  Combinations = itertools.combinations(CameraIds, 2)
  for C0, C1 in Combinations:
    PhysicalDistance = np.linalg.norm(TranslationVs[C0] - TranslationVs[C1])
    MaxPhysicalDistance = max(MaxPhysicalDistance, PhysicalDistance)
  return MaxPhysicalDistance

def calcFOVsXY(ResolutionXY, IntrinsicM):
  w  = ResolutionXY[0]
  h  = ResolutionXY[1]
  fx = IntrinsicM[0,0]
  fy = IntrinsicM[1,1]
  FOVx = math.atan2(w, 2*fx)
  FOVy = math.atan2(h, 2*fy)
  return (FOVx, FOVy)

def checkPerpendicularityToBaseline(CameraIds, TranslationVs, RotationMs, Epsilon):
  print("Checking if camera axes are perpendicular to baseline...")
  AllCorrect = True

  NumCams = len(CameraIds)
  BaselineVector   = TranslationVs[CameraIds[0]] - TranslationVs[CameraIds[NumCams-1]]
  CameraAxisVector = np.array([[0], [0], [1]])

  for CamId in CameraIds:
    CameraVector = np.matmul(RotationMs[CamId], CameraAxisVector)
    D = float(np.dot(np.transpose(BaselineVector), CameraVector))
    Correct = D < Epsilon
    print("Camera Cam " + ("_IS_" if Correct else "_IS NOT_") + f" perpendicular to baseline (with dot product = {D})")
    if not Correct: AllCorrect = False
  return Correct

def AllmostZero(v):
    eps = 1e-7
    return abs(v) < eps

def RotationMatrixToEulerAngles(R):
    yaw   = 0.0
    pitch = 0.0
    roll  = 0.0
    
    if AllmostZero( R[0,0] ) and AllmostZero( R[1,0] ) :
        yaw = np.arctan2( R[1,2], R[0,2] )
        if R[2,0] < 0.0:
            pitch = np.pi/2
        else:
            pitch = -np.pi/2
        roll = 0.0
    else:
        yaw = np.arctan2( R[1,0], R[0,0] )
        if AllmostZero( R[0,0] ) :
            pitch = np.arctan2( -R[2,0], R[1,0] / np.sin(yaw) )
        else:
            pitch = np.arctan2( -R[2,0], R[0,0] / np.cos(yaw) )
        
        roll = np.arctan2( R[2,1], R[2,2] )
    
    euler = np.array( [yaw, pitch, roll] )
    
    return np.rad2deg(euler)

def VSRStoJSON(TranslationV, RotationM):
  ExtrinsicM = np.array([
    [RotationM[0][0], RotationM[0][1], RotationM[0][2], TranslationV[0]],
    [RotationM[1][0], RotationM[1][1], RotationM[1][2], TranslationV[1]],
    [RotationM[2][0], RotationM[2][1], RotationM[2][2], TranslationV[2]]],
    dtype=np.float64)
   
  permute = np.array([ 
    [0, 0, 1], 
    [-1, 0, 0], 
    [0, -1, 0] ] )
   
  scale = 1  
  RotationMatrix   = np.transpose( permute.dot(ExtrinsicM[:,0:3] ).dot( np.transpose(permute) ) )
  Position         = scale * permute.dot(ExtrinsicM[:,3])
  EulerAngles      = RotationMatrixToEulerAngles(RotationMatrix)
  
  return Position, EulerAngles

@my_jit(nopython=True)
def calcFundamentalMatrixGeometricMean(m1, F, m0):
    d1, d2 = m0.shape
    error = 0
    point_err = -1*np.ones((d1, 1))
    numofpoints = 0
    Ft = np.transpose(F)
    
    for n in range(d1):
        if (m0[n,2] == 1) and (m1[n,2] == 1):
            l0 = F.dot(np.transpose(m0[n,0:3]))
            l1 = (Ft).dot(np.transpose(m1[n,0:3]))
            e = (m1[n,0:3]).dot(l0)
            f = (m0[n,0:3]).dot(l1)
            point_err[n,0] = (abs(e)*(1/np.sqrt(l0[0]*l0[0]+l0[1]*l0[1])))
            
            error = error + point_err[n,0]
            numofpoints = numofpoints + 1

    if numofpoints > 0: error = error / numofpoints          
    return (error, point_err)
  
def calcFundamentalMatrix(A, B):    
    F = np.eye(3)
    F[0,0]=(-1)**(1+1)*np.linalg.det([A[1,:],A[2,:],B[1,:],B[2,:]])
    F[0,1]=(-1)**(2+1)*np.linalg.det([A[0,:],A[2,:],B[1,:],B[2,:]])
    F[0,2]=(-1)**(3+1)*np.linalg.det([A[0,:],A[1,:],B[1,:],B[2,:]])
    F[1,0]=(-1)**(1+2)*np.linalg.det([A[1,:],A[2,:],B[0,:],B[2,:]])
    F[1,1]=(-1)**(2+2)*np.linalg.det([A[0,:],A[2,:],B[0,:],B[2,:]])
    F[1,2]=(-1)**(3+2)*np.linalg.det([A[0,:],A[1,:],B[0,:],B[2,:]])
    F[2,0]=(-1)**(1+3)*np.linalg.det([A[1,:],A[2,:],B[0,:],B[1,:]])
    F[2,1]=(-1)**(2+3)*np.linalg.det([A[0,:],A[2,:],B[0,:],B[1,:]])
    F[2,2]=(-1)**(3+3)*np.linalg.det([A[0,:],A[1,:],B[0,:],B[1,:]])
    return F

#==============================================================================================================================================================
