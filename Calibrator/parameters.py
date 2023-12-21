import numpy as np
import copy
import json
import datetime
import enum
import os
from scipy.spatial.transform import Rotation

import utils


#==============================================================================================================================================================
# CameraParameters
#==============================================================================================================================================================
class CameraParameters(object):

  def __init__(self) -> None:
    #Suffix: V-vector, M-matrix, Q-quaternion
    self._Name              = None
    self._ProjectionType    = None
    self._TranslationV      = np.empty(shape=(0))
    self._RotationV         = np.empty(shape=(0))
    self._RotationM         = np.empty(shape=(0))
    self._RotationQ         = np.empty(shape=(0))
    self._ResolutionXY      = np.empty(shape=(0)) 
   
    self._FocalXY           = np.empty(shape=(0))
    self._PrinciplePointXY  = np.empty(shape=(0))

    self._IntrinsicM        = np.empty(shape=(0))
    self._ExtrinsicM        = np.empty(shape=(0)) 
    return

  #def __repr__(self) -> str:
  #  pass

  @property
  def CameraId(self): return self._CameraId
  @CameraId.setter
  def CameraId(self, CameraId): self._CameraId = CameraId

  @property
  def ResolutionXY(self): return self._ResolutionXY
  @ResolutionXY.setter
  def ResolutionXY(self, ResolutionXY): self._ResolutionXY = ResolutionXY

  @property
  def IntrinsicM(self): return self._IntrinsicM
  @IntrinsicM.setter
  def IntrinsicM(self, IntrinsicM): self._IntrinsicM = IntrinsicM

  @property
  def RotationV(self): return self._RotationV
  @RotationV.setter
  def RotationV(self, RotationV):
    self._RotationV = RotationV
    self._RotationM = Rotation.from_euler('xyz', RotationV, degrees=True).as_matrix()
    self._RotationQ = Rotation.from_euler('xyz', RotationV, degrees=True).as_quat()

  @property
  def RotationM(self): return self._RotationM
  @RotationM.setter
  def RotationM(self, RotationM):
    self._RotationM = RotationM
    self._RotationV = Rotation.from_matrix(RotationM).as_euler('xyz', degrees=True)
    self._RotationQ = Rotation.from_matrix(RotationM).as_quat()

  @property
  def RotationQ(self): return self._RotationQ
  @RotationQ.setter
  def RotationQ(self, RotationQ):
    self._RotationQ = RotationQ
    self._RotationV = Rotation.from_quat(RotationQ).as_euler('xyz', degrees=True)
    self._RotationM = Rotation.from_quat(RotationQ).as_matrix()

  @property
  def TranslationV(self): return self._TranslationV
  @TranslationV.setter
  def TranslationV(self, TranslationV): self._TranslationV = TranslationV


  @property
  def ExtrinsicM(self): return self._ExtrinsicM


  @property
  def ProjectionM(self):
    return np.matmul(self.IntrinsicM, self.ExtrinsicM)

  def scale(self, NewResolutionXY) -> bool:
    CurAspectRatio = self._ResolutionXY[0] / self._ResolutionXY[1]
    NewAspectRatio = NewResolutionXY   [0] / NewResolutionXY   [1]
    CanScale = np.isclose(CurAspectRatio, NewAspectRatio)
    if CanScale:
      DecimationFactorX = self.ResolutionXY[0] / NewResolutionXY[0]
      DecimationFactorY = self.ResolutionXY[1] / NewResolutionXY[1]
      self._IntrinsicM[0,:] = self._IntrinsicM[0,:] / DecimationFactorX
      self._IntrinsicM[1,:] = self._IntrinsicM[1,:] / DecimationFactorY
    return CanScale
  

  def writeTo(self, ContentJSON: dict) -> dict:
    ContentJSON = ContentJSON.copy()
    Position, Rotation = utils.VSRStoJSON(self._TranslationV, self._RotationM)
  
    ContentJSON['Name'            ] = self._Name
    ContentJSON['Position'        ] = Position.tolist()
    ContentJSON['Rotation'        ] = Rotation.tolist()
    ContentJSON['Resolution'      ] = self._ResolutionXY.tolist()
    ContentJSON['Projection'      ] = self._ProjectionType
    ContentJSON['Focal'           ] = self._FocalXY.tolist()
    ContentJSON['Principle_point' ] = self._PrinciplePointXY.tolist()
    ContentJSON['Depth_range'     ] = self._DepthRange.tolist()

    ContentJSON['BitDepthColor'   ] = 8
    ContentJSON['BitDepthDepth'   ] = 16
    ContentJSON['ColorSpace'      ] = "YUV420"
    ContentJSON['DepthColorSpace' ] = "YUV420"

    return ContentJSON

  def readFrom(self, ContentJSON:dict) -> bool:
    self._Name              = str     (ContentJSON['Name'           ]                     )
    self._TranslationV      = np.array(ContentJSON['Position'       ],  dtype=np.float64  )
    self._RotationV         = np.array(ContentJSON['Rotation'       ],  dtype=np.float64  )
    self._ResolutionXY      = np.array(ContentJSON['Resolution'     ],  dtype=np.int32    ) 
    self._ProjectionType    = str     (ContentJSON['Projection'     ]                     )
    self._FocalXY           = np.array(ContentJSON['Focal'          ],  dtype=np.float64  )
    self._PrinciplePointXY  = np.array(ContentJSON['Principle_point'],  dtype=np.float64  )
    self._DepthRange        = np.array(ContentJSON['Depth_range'    ],  dtype=np.float64)
 
    self._RotationM = Rotation.from_euler('xyz', self._RotationV, degrees=True).as_matrix()
    self._RotationQ = Rotation.from_euler('xyz', self._RotationV, degrees=True).as_quat()

    self._IntrinsicM = np.array([
      [self._FocalXY[0], 0, self._PrinciplePointXY[0]], 
      [0, self._FocalXY[1], self._PrinciplePointXY[1]], 
      [0,                0,                        1]], 
      dtype=np.float64)
    
    self._ExtrinsicM = np.array([
      [self._RotationM[0][0], self._RotationM[0][1], self._RotationM[0][2], self._TranslationV[0]],
      [self._RotationM[1][0], self._RotationM[1][1], self._RotationM[1][2], self._TranslationV[1]],
      [self._RotationM[2][0], self._RotationM[2][1], self._RotationM[2][2], self._TranslationV[2]],
      [                    0,                     0,                     0,                    1]],
      dtype=np.float64)
    
    return True

#==============================================================================================================================================================
# SystemParameters
#==============================================================================================================================================================
class SystemParameters(object):
  
  def __init__(self, CameraIds:list) -> None:
    self._CameraParameters    = {}
    self._CameraIds           = [f'v{id}' for id in CameraIds]

    return    

  # @property
  # def SystemName(self): return self._SystemName
  # @SystemName.setter
  # def SystemName(self, SystemName): self._SystemName = SystemName

  @property
  def CameraIds(self): return self._CameraIds
  @CameraIds.setter
  def CameraIds(self, CameraIds): self._CameraIds = CameraIds

  # @property
  # def MainCamId(self): return self._MainCamId
  # @MainCamId.setter
  # def MainCamId(self, MainCamId): self._MainCamId = MainCamId

  @property
  def Params(self): return self._CameraParameters
  @Params.setter
  def Params(self, Params): self._CameraParameters = Params

  @property
  def ResolutionXYs(self): 
    ResolutionXYs = { C : self.Params[C].ResolutionXY for C in self.CameraIds }
    return ResolutionXYs
  @ResolutionXYs.setter
  def ResolutionXYs(self, ResolutionXY):
    for P in self._CameraParameters.values(): P.ResolutionXY = ResolutionXY

  @property
  def IntrinsicMs(self): 
    IntrinsicMs = { C : self.Params[C].IntrinsicM for C in self.CameraIds }
    return IntrinsicMs

  @property
  def DistortionVs(self): 
    DistortionVs = { C : self.Params[C].DistortionV for C in self.CameraIds }
    return DistortionVs

  @property
  def RotationVs(self): 
    RotationVs = { C : self.Params[C].RotationV for C in self.CameraIds }
    return RotationVs

  @property
  def RotationMs(self): 
    RotationMs = { C : self.Params[C].RotationM for C in self.CameraIds }
    return RotationMs
  
  @property
  def RotationQs(self): 
    RotationQs = { C : self.Params[C].RotationQ for C in self.CameraIds }
    return RotationQs
  @RotationQs.setter
  def RotationQs(self, RotationQs: dict):
    for CamId, P in self._CameraParameters.items(): P.RotationQ = RotationQs[CamId]

  @property
  def TranslationVs(self): 
    TranslationVs = { C : self.Params[C].TranslationV for C in self.CameraIds }
    return TranslationVs
  @TranslationVs.setter
  def TranslationVs(self, TranslationVs: dict):
    for CamId, P in self._CameraParameters.items(): P.TranslationV = TranslationVs[CamId]

  def append(self, CamParam:CameraParameters) -> None:
    CameraId = CamParam.CameraId
    self._CameraIds.append(CameraId)
    self._CameraParameters[CameraId] = CamParam
    return

  def scale(self, NewResolution) -> bool:
    AllCorrect = True
    for CameraId in self.CameraIds:
      Result = self._CameraParameters[CameraId].scale(NewResolution)
      if not Result: AllCorrect = False
    return AllCorrect

  def calcMaxDistanceBetweenCameras(self):
    MaxDistance = utils.calcMaxDistanceBetweenCameras(self.CameraIds, self.TranslationVs)
    return MaxDistance

  def writeTo(self, outSystemParamsPath: str) -> bool:

    SystemParamsJSON = {'cameras':[]}
    CamParamsJSON = {}

    SystemParamsJSON['informative'] = {
      'generated_by': 'PUT Calibrator'
    }

    for CamId in self._CameraIds:
      CamParams = self._CameraParameters[CamId]
      CamParamsJSON = CamParams.writeTo(CamParamsJSON)
      SystemParamsJSON['cameras'].append(CamParamsJSON)

    

    SystemParamsStr = json.dumps(SystemParamsJSON, indent=2)
    with open(outSystemParamsPath, 'w') as SystemParamsFile:
       SystemParamsFile.write(SystemParamsStr)

    # ContentJSON = {}
    # ContentJSON["TimeStamp"] = datetime.datetime.now().isoformat()
    # ContentJSON["SystemName" ] = str (self.SystemName )
    # ContentJSON["CameraIds"] = list(self.CameraIds)
    # ContentJSON["MainCamId"] = str (self.MainCamId)
    # ContentJSON["Params"   ] = dict(              )
    # for Cam in self.CameraIds:
    #   ContentJSON["Params"][Cam] = self._CameraParameters[Cam].writeTo()
    # StrJSON = json.dumps(ContentJSON, indent=2)
    # return StrJSON
    return True

  def readFrom(self, inSystemParamsPath: str) -> bool:

    with open(inSystemParamsPath, "r") as SystemParamsFile: 
      SystemParamsStr = SystemParamsFile.read()
      SystemParamsJSON = json.loads(SystemParamsStr)

    for CamParamsJSON in SystemParamsJSON['cameras']:
      CamName = CamParamsJSON['Name']
      if CamName in self._CameraIds: # Load only specified cameras
        CamParams = CameraParameters()
        CamParams.readFrom(CamParamsJSON)
        self._CameraParameters[CamName] = CamParams
    return True






#==============================================================================================================================================================
