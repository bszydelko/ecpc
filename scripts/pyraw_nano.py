# SPDX-License-Identifier: GPL-3.0
# Author: Jakub Stankowski, st2048@gmail.com

#==============================================================================================================================================================

import os
import enum
import numpy as np

#==============================================================================================================================================================

class ePicType(enum.IntEnum):
  Unknown = 0
  
  RGB_BEG = 100
  RGB     = 100
  BGR     = 101
  RGB_END = 199
  
  YUV_BEG = 200
  YCbCr   = 200
  YUV     = 200
  BT709   = 201
  YUV_END = 299

  BAY_BEG = 300
  Bayer   = 300
  BAY_END = 300

class eMode(enum.IntEnum):
  Unknown = enum.auto()
  Read    = enum.auto()
  Write   = enum.auto()
  Append  = enum.auto()

class eColorSpace(enum.IntEnum):
  Unknown = 0
  BT601   = 601
  BT709   = 709

#==============================================================================================================================================================

class xSeq(object):  

  @staticmethod
  def _determineCmpSizes(BaseSizeWH, PicType:ePicType, ChromaFormat:int):
    CmpSizesWH = None

    if PicType == ePicType.Unknown:
      return None

    elif PicType.value>=ePicType.RGB_BEG.value and PicType.value<=ePicType.RGB_END.value:
      CmpSizesWH = [BaseSizeWH, BaseSizeWH, BaseSizeWH]
    
    elif PicType.value>=ePicType.YUV_BEG.value and PicType.value<=ePicType.YUV_END.value:
      if ChromaFormat == 400:
        CmpSizesWH = [BaseSizeWH]
      else:
        ChromaSizeWH = {
          444: lambda : BaseSizeWH,
          422: lambda : (int(BaseSizeWH[0]//2), BaseSizeWH[1]),
          420: lambda : (int(BaseSizeWH[0]//2), int(BaseSizeWH[1]//2)),
        }[ChromaFormat]()
        CmpSizesWH = [BaseSizeWH, ChromaSizeWH, ChromaSizeWH]

    elif PicType.value>=ePicType.BAY_BEG.value and PicType.value<=ePicType.BAY_END.value:
      CmpSizesWH = [BaseSizeWH]
  
    return CmpSizesWH

  @staticmethod
  def _calcCmpNumPels(SizesWH):
    NumPels = [int(SizeWH[0]) * int(SizeWH[1]) for SizeWH in SizesWH]
    return np.array(NumPels, dtype=np.int64)

  def _unpackCmps(self, Buffer:bytes) -> list:
    Cmps   = []
    Offset = 0
    for CmpIdx in range(len(self._SizesWH)):
      CmpSizeWH = self._SizesWH[CmpIdx]
      ReadCmp   = np.frombuffer(Buffer, dtype=self._FileDataType, count=self._FileCmpNumPels[CmpIdx], offset=Offset)
      Offset += self._FileCmpNumBytes[CmpIdx]
      Cmps.append(np.reshape(ReadCmp, (CmpSizeWH[1], CmpSizeWH[0])))
    return Cmps
  
  def _packCmps(self, Pic) ->np.array:
    FileBuffer = bytearray()
    for CmpIdx in range(len(self._SizesWH)):
      FileBuffer += np.ravel(Pic[CmpIdx]).tobytes()
    return FileBuffer

  #--------------------------------------------------------------------------------------------------------------------------------------------------------------

  def __init__(self, Width:int, Height:int, BitDepth:int):
    self._SizeBaseWH      = (Width, Height)
    self._SizesWH         = []
    self._BitsPerSample   = BitDepth
    self._BytesPerSample  = 1 if BitDepth <= 8 else 2
    self._FileDataType    = np.uint8 if self._BytesPerSample==1 else np.uint16
    self._ColorSpace      = None    
    self._ChromaFormat    = None

    self._FileCmpNumPels  = None
    self._FileCmpNumBytes = None
    self._FileImgNumBytes = None

    self._FileName      = None
    self._FileMode      = None
    self._FileHandle    = None
    self._FileNumFrames = None
    return

  #--------------------------------------------------------------------------------------------------------------------------------------------------------------

  @property
  def Width    (self): return self._SizeBaseWH[0]
  @property
  def Height   (self): return self._SizeBaseWH[1]
  @property
  def BitDepth (self): return self._BitsPerSample
  @property
  def DataType (self): return self._FileDataType
  @property
  def NumFrames(self): return self._FileNumFrames

  def openFile(self, FilePath:str, FileMode:eMode):
    '''Opens a RAW file. Possible modes = [eMode.Read, eMode.Write, eMode.Append]'''
    if (self._FileMode == eMode.Read and not os.path.exists(FilePath)): return None
  
    self._FileName = FilePath
    self._FileMode = FileMode
    if  (self._FileMode == eMode.Read  ): self._FileHandle = open(self._FileName, "rb")
    elif(self._FileMode == eMode.Write ): self._FileHandle = open(self._FileName, "wb")
    elif(self._FileMode == eMode.Append): self._FileHandle = open(self._FileName, "ab")

    if(self._FileMode == eMode.Read and self._FileMode == eMode.Append):
      FileSize = os.path.getsize(FilePath)
      self._FileNumFrames = int(FileSize // self._FileImgNumBytes)
    else:
      self._FileNumFrames = 0

    return not self._FileHandle.closed

  def closeFile(self):
    '''Closes previously opened RAW file'''
    self._FileHandle.close()
    self._FileHandle    = None
    self._FileName      = ""
    self._FileMode      = eMode.Unknown
    self._FileNumFrames = 0
    return True

  def seekPic(self, FrameNumber:int):
    '''Seek selected frame in sequence file'''
    Offset = self._FileImgNumBytes * FrameNumber
    self._FileHandle.seek(Offset, 0)
    return True
  
#==============================================================================================================================================================
# xSeqYUV
#==============================================================================================================================================================
class xSeqYUV(xSeq):
  DefColorSpace = eColorSpace.BT709

  def __init__(self, Width:int, Height:int, BitDepth:int, ChromaFormat:int):
    super().__init__(Width, Height, BitDepth)

    self._SizesWH         = xSeq._determineCmpSizes(self._SizeBaseWH, ePicType.YCbCr, ChromaFormat)
    self._CmpOrder        = "YCbCr"
    self._ColorSpace      = None
    self._ChromaFormat    = ChromaFormat

    self._FileCmpNumPels  = self._calcCmpNumPels(self._SizesWH)
    self._FileCmpNumBytes = self._FileCmpNumPels * self._BytesPerSample
    self._FileImgNumBytes = sum(self._FileCmpNumBytes)
    return


  @staticmethod
  def _convert4XXto444(YUV4XX:map, ChromaFormat:int) -> map:
    #take luma directly
    YUV444 = { 0 : YUV4XX[0] }
    #process chroma
    for CmpIdx in range(1, 3):
      if  (ChromaFormat == 444): YUV444[CmpIdx] = YUV4XX[CmpIdx]
      elif(ChromaFormat == 422): YUV444[CmpIdx] = np.repeat(YUV4XX[CmpIdx], 2, axis = 1)
      elif(ChromaFormat == 420): YUV444[CmpIdx] = np.repeat(np.repeat(YUV4XX[CmpIdx], 2, axis = 0), 2, axis = 1)
    #return 444
    return YUV444

#--------------------------------------------------------------------------------------------------------------------------------------------------------------

  def readPicYUV(self) -> np.ndarray:
    '''
    Reads entire picture in YCbCr colorspace and returns as 3D numpy array.
    In case of 420 and 422 chroma format, chroma components are upsampled to Luma size - returned picture has format 444.
    Returned array shape = [y][x][3]
    '''
    #read frame bytes
    FileBuffer = self._FileHandle.read(self._FileImgNumBytes)
    #bytes to ndarray
    Cmp4XX = self._unpackCmps(FileBuffer)
    #convert to 444
    Cmp444 = self._convert4XXto444(Cmp4XX, self._ChromaFormat)   
    #convert to [y][x][3] array
    PicYUV = np.stack(list(Cmp444.values()), 2)
    #gimme results
    return PicYUV

#--------------------------------------------------------------------------------------------------------------------------------------------------------------

  def readCmpLuma(self) -> np.ndarray:
    '''Reds only Luma component and returns as 2D numpy array with shape [y][x]'''
    #read frame bytes
    FileBuffer = self._FileHandle.read(self._FileImgNumBytes)
    #bytes to ndarray
    Cmp4XX = self._unpackCmps(FileBuffer)
    #get luma
    Luma = Cmp4XX[0]
    return Luma

#==============================================================================================================================================================

def calcNumFramesInFile(Width:int, Height:int, BitDepth:int, PicType:ePicType, ChromaFormat:int, FileSize:int):
  '''Calculates number of frames in file'''
  SizeBaseWH      = (Width, Height)
  SizesCmpWH      = xSeq._determineCmpSizes(SizeBaseWH, PicType, ChromaFormat)
  BytesPerSample  = 1 if BitDepth <= 8 else 2
  FileCmpNumPels  = xSeq._calcCmpNumPels(SizesCmpWH)
  FileCmpNumBytes = FileCmpNumPels * BytesPerSample
  FileImgNumBytes = sum(FileCmpNumBytes)
  return int(FileSize // FileImgNumBytes)

#==============================================================================================================================================================

def imreadYUV(FilePath:str, Width:int, Height:int, BitDepth:int, ChromaFormat:int, FrameIdx:int) -> np.ndarray:
  if (not os.path.exists(FilePath)): print("File {} does not exist!".format(FilePath)); return None
  FileSize        = os.path.getsize(FilePath)
  NumFramesInFile = calcNumFramesInFile(Width, Height, BitDepth, ePicType.YCbCr, ChromaFormat, FileSize)
  if (FrameIdx >= NumFramesInFile): print("File contains {} frames --> cannot read frame {}!".format(NumFramesInFile, FrameIdx)); return None
  
  Seq = xSeqYUV(Width, Height, BitDepth, ChromaFormat)
  Seq.openFile(FilePath, eMode.Read)
  if (FrameIdx != 0): Seq.seekPic(FrameIdx)
  Frame = Seq.readPicYUV()
  Seq.closeFile()
  del Seq
  return Frame

#--------------------------------------------------------------------------------------------------------------------------------------------------------------

def imreadLuma(FilePath:str, Width:int, Height:int, BitDepth:int, ChromaFormat:int, FrameIdx:int) -> np.ndarray:
  if (not os.path.exists(FilePath)): print("File {} does not exist!".format(FilePath)); return None
  FileSize        = os.path.getsize(FilePath)
  NumFramesInFile = calcNumFramesInFile(Width, Height, BitDepth, ePicType.YCbCr, ChromaFormat, FileSize)
  if (FrameIdx >= NumFramesInFile): print("File contains {} frames --> cannot read frame {}!".format(NumFramesInFile, FrameIdx)); return None
  
  Seq = xSeqYUV(Width, Height, BitDepth, ChromaFormat)
  Seq.openFile(FilePath, eMode.Read)
  if (FrameIdx != 0): Seq.seekPic(FrameIdx)
  Luma = Seq.readCmpLuma()
  Seq.closeFile()
  del Seq
  return Luma

#--------------------------------------------------------------------------------------------------------------------------------------------------------------