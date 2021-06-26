# -*- coding: utf-8 -*-

import pathlib # change to pathlib from Python 3.4 instead of os
import tifffile
import numpy as np
import cv2

def import_video(inputpath):
    """
        imports video from path
        possible inputs:
            - videofile (.avi/.mov/.mp4)
            - folder with .tif-files (select one tif-file in folder)
    """
    if type(inputpath) == str:
        inputpath = pathlib.Path(inputpath) #convert string input to pathlib path
    
    extension = inputpath.suffix
    if extension not in ['.tif','.avi','.mov','.mp4']:
        print('imputfile not supported. Choose a .tif/.avi/.mov/.mp4')
        return
    
    print('importing video from path:', inputpath, "\nwith the file extension:", extension)
    
    if extension == '.tif':
        rawImageStack, videometa = read_imagestack(inputpath)
    else:
        rawImageStack, videometa = read_videofile(inputpath)

    videometa["inputpath"] = inputpath
    print('videometa:', videometa)
    return rawImageStack, videometa
    
def read_imagestack(inputpath, *args, **kwargs):
    """
        reads folder with sequence of tif-files
    """

    inputtifs = list(inputpath.parent.glob('*.tif'))  # or use sorted instead of list?    

    rawImageStack = tifffile.imread(inputtifs, pattern = '')
    rawImageStack = rawImageStack.astype(np.float32)    #convert as cv2 needs float32 for templateMatching

    videometa = get_videoinfos_file(inputpath)
    videometa['frameCount']=len(inputtifs)
    videometa['frameWidth']=rawImageStack.shape[1]
    videometa['frameHeight']=rawImageStack.shape[2]
    videometa['input_type'] = 'tifstack'
    
    if ('Blackval' or 'Whiteval') not in videometa.keys():
        videometa["Blackval"], videometa["Whiteval"] = np.percentile(rawImageStack[0], (0.1, 99.9))  #set default values if no infos defined in videoinfos file

    return rawImageStack, videometa
    
def get_videoinfos_file(inputpath):
    """
        reads dict from file videoinfos.txt and sets values in videometa
    """
    videometa = {}
    path_videoinfos = inputpath.parent / "videoinfos.txt"
    if path_videoinfos.is_file():
        # set metadata from file if videoinfos.txt exists
        print("videoinfos.txt exists in inputfolder, reading parameters.")
        #videometa = self.get_videoinfos_file()    
    
        filereader = (path_videoinfos).open("r")
        videoinfos_file = eval(filereader.read())
        filereader.close()
        for key, value in videoinfos_file.items():
            videometa[key] = value
    return videometa
    
def read_videofile(inputpath):
    """
        reads single .mp4/.avi/.mov file
    """
    cap = cv2.VideoCapture(str(inputpath))

    frameCount = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frameWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frameHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    videofps = cap.get(cv2.CAP_PROP_FPS)
    
    rawImageStack = np.empty((frameCount, frameHeight, frameWidth), np.dtype('uint8'))

    fc = 0
    ret = True

    while (fc < frameCount  and ret):
        ret, frame = cap.read()
        rawImageStack[fc] = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        fc += 1    
    
    videometa = {'frameCount':frameCount,'frameWidth':frameWidth,'frameHeight':frameHeight,'fps':videofps}
    videometa["Blackval"], videometa["Whiteval"] = np.percentile(rawImageStack[0], (0.1, 99.9))
    videometa["input_type"] = 'videofile'

    cap.release()
    return rawImageStack, videometa
    
def get_first_frame(inputpath):

    extension = inputpath.suffix
    if extension not in ['.tif','.avi','.mov','.mp4']:
        print('imputfile not supported. Choose a .tif/.avi/.mov/.mp4')
        return
    
    if extension == '.tif':
        first_file = list(inputpath.parent.glob('*.tif')) [0]
        first_image = tifffile.imread(first_file, pattern = '')
    else:

        cap = cv2.VideoCapture(str(inputpath))
        ret, first_image = cap.read()
        cap.release()
    
    return first_image