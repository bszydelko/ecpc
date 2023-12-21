
import os
import numpy as np
import multiprocessing as mp

from scipy import optimize
from scipy.spatial.transform import Rotation

import parameters
import utils

class Calibrator(object):
    def __init__(self, args) -> None:
        self._numberOfAllCameras        = args.ncams
        self._camerasIdsToCalibrate     = args.camrange
        self._numberOfReferencePoints   = args.npoints
        self._referencePointsPath       = args.r
        self._initCamParamsPath         = args.i
        self._outCamParamsPath          = args.o
        
        #self.visualise = True TODO

        self._cameraParameters          = None
        self._currentCamParams          = None
        self._allReferencePoints        = None
        self._usedReferencePoints       = None

        self._error       = 10000
        
        # Handle cameras to calibrate
        if str(self._camerasIdsToCalibrate)[0] == '[' and str(self._camerasIdsToCalibrate)[-1] == ']':
            tmp_list = self._camerasIdsToCalibrate[1:-1].split(',')
            self._camerasIdsToCalibrate = list(map(int, tmp_list))
        else:
            start, step, stop = tuple(self._camerasIdsToCalibrate.split(":"))
            self._camerasIdsToCalibrate = np.arange(int(start), int(stop)+1, int(step))
        self._numOfCamerasToCalibrate = len(self._camerasIdsToCalibrate)

        # Load initial cam params
        self._cameraParameters = parameters.SystemParameters(self._camerasIdsToCalibrate)
        self._cameraParameters.readFrom(self._initCamParamsPath)
    
        self._readReferencePoints()
        
        # Put rotations and translations into one list
        self._optimParam = []
        RotationQs = self._cameraParameters.RotationQs
        TranslationVs = self._cameraParameters.TranslationVs
        for Cam in self._camerasIdsToCalibrate:
            self._optimParam.extend(RotationQs      ['v'+str(Cam)][:])
            self._optimParam.extend(TranslationVs   ['v'+str(Cam)][:])

        # Create K 4x4 matrices from 3x3 intrinsics
        self.K = np.full((self._numOfCamerasToCalibrate,4,4),np.eye(4))
        for count, cam in enumerate(self._camerasIdsToCalibrate):
            self.K[count][0:3, 0:3] = self._cameraParameters.IntrinsicMs['v'+str(cam)]

        #if self._visualise: self._initVisualiser()
        return
 
# ===================================================================================================
# Main part         
# ===================================================================================================         
    def run(self, iterations):
        for global_it in range(0, iterations):
            
            optimResult = optimize.minimize(\
                        self._minFunctionExtrinsic, \
                        self._optimParam, \
                        method='L-BFGS-B',\
                        options = {'disp': True, 'ftol':0.000000001, 'maxfun':1000*len(self._optimParam), 'maxcor': 100, 'maxls': 20})    

            deletedPoints = self._rejectReferencePoints()
            
            self._updateParams(optimResult['x'])
            self._cameraParameters.writeTo(self._outCamParamsPath.replace('.json', f'_it{global_it}.json'))
        
            print('===========================================================================')
            print(f'[{global_it}] global iteration ended.') 
            print(f'[{deletedPoints}] reference points rejected')
            print(f'Saving params to {self._outCamParamsPath.replace(".json", "_it"+str(global_it)+".json")}.')
            print('===========================================================================\n')
            
            if deletedPoints == 0: break

        return True
    
# ===================================================================================================
#  Functions
# ===================================================================================================
    def _updateParams(self, solution: list) -> bool:
        RotationQs      = {}
        TranslationVs   = {}

        for i, CamId in enumerate(self._camerasIdsToCalibrate):
            RotationQs[f'v{CamId}'] = [solution[7*i], solution[7*i+1], solution[7*i+2], solution[7*i+3]]
            TranslationVs[f'v{CamId}']  = np.array([solution[7*i+4], solution[7*i+5], solution[7*i+6]])

        self._cameraParameters.RotationQs = RotationQs
        self._cameraParameters.TranslationVs = TranslationVs

        return True

    def _readReferencePoints(self) -> bool:
        # Read calibration points
        with open(self._referencePointsPath) as f:
            points_array = np.loadtxt(f, delimiter='\t')
            assert points_array.shape == (self._numberOfReferencePoints, self._numberOfAllCameras * 3)
            
            # Convert array of points into subsets of points for each camera
            self._allReferencePoints = np.zeros((self._numberOfAllCameras, self._numberOfReferencePoints, 3))
            for cam in range(self._numberOfAllCameras):   
                self._allReferencePoints[cam] = points_array[:,cam*3:(cam*3)+3]
            f.close()

        # Use only reference points for cameras to calibrate   
        self._usedReferencePoints = np.zeros((self._numOfCamerasToCalibrate,self._numberOfReferencePoints,3))
        for count, cam in enumerate(self._camerasIdsToCalibrate):
            self._usedReferencePoints[count] = self._allReferencePoints[cam]

        # Probably remove the closest calibration points to frame boundaries
        for c in range(self._numOfCamerasToCalibrate):
            for p in range(self._numberOfReferencePoints):
                if self._usedReferencePoints[c][p][0] > 0:
                    if self._pointCondition(c, p):
                           self._usedReferencePoints[c][p] = np.zeros((1,3))

        return True
       
    def _rejectReferencePoints(self):
        k = 0
        deletedPoints = 0
        for i in range(self._numOfCamerasToCalibrate):
            for j in range(i+1,self._numOfCamerasToCalibrate):
                if i is not j:
                    for p in range(self._numberOfReferencePoints):
                        if self._point_err_2[p,k] >  10 * self._error:
                            self._usedReferencePoints[i,p,0:3] = np.array([-1.0,-1.0,0])
                            self._usedReferencePoints[j,p,0:3] = np.array([-1.0,-1.0,0])
                            deletedPoints = deletedPoints + 1
                            print('Cams ',i,' and ',j, ' point number ',p,' error ', self._point_err_2[p,k],'\n')
                    k = k+1
        return deletedPoints

    def _minFunctionExtrinsic(self, optimParam):
        E = np.full((self._numOfCamerasToCalibrate,4,4),np.zeros(4))
        P = np.full((self._numOfCamerasToCalibrate,4,4),np.zeros(4))
        
        for i in range(self._numOfCamerasToCalibrate):
            # Unpack quaterions and rotations for each camera
            RotationQ = [optimParam[7*i], optimParam[7*i+1], optimParam[7*i+2], optimParam[7*i+3]]
            RotationM = Rotation.from_quat(RotationQ).as_matrix()
            TranslationV  = np.array([optimParam[7*i+4], optimParam[7*i+5], optimParam[7*i+6]])
            
            E[i,:,:] = self._extrinsicMatrix(TranslationV, RotationM)
            P[i,:,:] = self._projectionMatrix(self.K[i,:,:], E[i,:,:])
        
        
        self._point_err_2 = np.zeros((self._numberOfReferencePoints, self._numOfCamerasToCalibrate*self._numOfCamerasToCalibrate-self._numOfCamerasToCalibrate))
        m = np.zeros((self._numOfCamerasToCalibrate, self._numberOfReferencePoints, 3))
        
        for c in range(self._numOfCamerasToCalibrate):
            m[c,:,:] = self._usedReferencePoints[c]
            
        er, self._point_err_2 = self._targetErrorAllCam(P)

        self._error = er

        return er 
    
    def _targetErrorAllCam(self, P):
        e = 0
        k = 0
        er = 0
        point_err = np.zeros((self._numberOfReferencePoints, self._numOfCamerasToCalibrate*self._numOfCamerasToCalibrate-self._numOfCamerasToCalibrate))
        
        for i in range(self._numOfCamerasToCalibrate):
            for j in range(i+1,self._numOfCamerasToCalibrate):
                if i is not j:
                    F = utils.calcFundamentalMatrix(P[j,:,:], P[i,:,:])
                    er, point_err[:,k:k+1] = \
                        utils.calcFundamentalMatrixGeometricMean(
                            self._usedReferencePoints[i,:,:], 
                            F,
                            self._usedReferencePoints[j,:,:]) 
                    e = e + er
                    k = k + 1

        e = e / k
        
        return (e, point_err)

    def _pointCondition(self, cam, p):
         return \
            self._usedReferencePoints[cam][p][0]    == 0 or \
            self._usedReferencePoints[cam][p][1]    == 0

    def _projectionMatrix(self, K, E):
        return np.matmul(K,E)
    
    def _extrinsicMatrix(self, TranslationV, RotationM):
        E           = np.eye(4)
        E[0:3,0:3]  = RotationM
        E[0:3,3]    = -1 * np.matmul(RotationM, TranslationV)

        return E
        
    def _extrinsicMatrixDers(self, TranslationV, RotationM):
        E           = np.eye(4)
        E[0:3, 0:3] = RotationM
        E[0:3, 3]   = np.transpose(TranslationV)
        
        return E