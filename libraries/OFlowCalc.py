# -*- coding: utf-8 -*-

import cv2
import math
import numpy as np
import time
from PyQt5.QtCore import QThread, pyqtSignal

"""
    currently offered methods for OFlow calculation (for 2 images)
    - Blockmatch (BM_single)
    - LucasKanade (LK_single)
    - GunnarFarnebäck (GF_single)
    
    for stack:
    - Blockmatch (BM_stack)

"""
# filter has to go somewhere else!

def LK_single(img_prev, img_curr):
    # insert cv2 code
    pass

def BM_single(img_prev, img_curr, max_shift, blockwidth):
    """
        gets optical flow by block matching between 2 images with parameters of max_shift and blockwidth
    """

    size_ver, size_hor = img_prev.shape[:2]
    MVs_ver = math.floor(size_ver/blockwidth)   # number of MVs in horizontal direction
    MVs_hor = math.floor(size_hor/blockwidth)
    
    # pad image to enable searching at edge
    img_curr = cv2.copyMakeBorder(img_curr,max_shift,max_shift,max_shift,max_shift,cv2.BORDER_REPLICATE)
      
    # prepare arrays for MVs (component X & Y)
    MotionVectorsX = np.zeros(shape = (MVs_ver,MVs_hor))
    MotionVectorsY = np.zeros(shape = (MVs_ver,MVs_hor))
    
    # iterate over blocks
    for rowidx in range(MVs_ver):   # np.arange or range? use numpy/ parallelize better!
        for colidx in range(MVs_hor):
            patternToFind = img_prev[rowidx*blockwidth:rowidx*blockwidth+blockwidth,colidx*blockwidth:colidx*blockwidth+blockwidth]
            searchRegion = img_curr[rowidx*blockwidth:rowidx*blockwidth+blockwidth+2*max_shift,colidx*blockwidth:colidx*blockwidth+blockwidth+2*max_shift]
                        
            MotionVectorsX[rowidx, colidx], MotionVectorsY[rowidx, colidx] = BM_getMV(patternToFind, searchRegion, max_shift)
        
    return MotionVectorsX, MotionVectorsY

def BM_getMV(patternToFind, searchRegion, max_shift, methodnr = 4):
    """
        gets single MV at specified region, works with cv2 matchTemplate, specify method with methodnr
    """
    methods = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR',
                'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']    
    method = eval(methods[methodnr])
    
    matchResult = cv2.matchTemplate(searchRegion, patternToFind, method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(matchResult)
    
    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        top_left = min_loc
    else:
        top_left = max_loc    
    
    # subtract max_shift, as center (= no movement) is situated at this coordinate
    xMotion = top_left[0] - max_shift
    yMotion = top_left[1] - max_shift
    
    return xMotion, yMotion


class BM_stack_thread(QThread):
    progressSignal = pyqtSignal(float)

    def __init__(self, imageStack, blockwidth, delay, max_shift):
        QThread.__init__(self)
        #self.stop_flag = False
        
        self.MotionVectorsAll = None
        self.imageStack = imageStack
        self.blockwidth = blockwidth
        self.delay = delay
        self.max_shift = max_shift
        
    def run(self):       
        print("Calculating Optical Flow of imagestack by means of Blockmatching")
        starttime = time.time() #for benchmarking...

        MotionVectorsAll = []

        total_frames = self.imageStack.shape[0] - self.delay
        
        for frame, (prev_img, curr_img) in enumerate(zip(self.imageStack, self.imageStack[self.delay:])):
            # iterate pairwise over frames, total pairs: number_frames - delay
            
            MotionVectorsX, MotionVectorsY = BM_single(prev_img, curr_img, self.max_shift, self.blockwidth)
            MotionVectorsAll.append((MotionVectorsX, MotionVectorsY))   # this can be definitely be done nicer with numpy
            
            self.progressSignal.emit((frame+1)/total_frames)

        endtime = time.time()
        print('Execution time in seconds:', (endtime - starttime))

        self.MotionVectorsAll = np.array(MotionVectorsAll)    
    
def BM_stack(imageStack, blockwidth, delay, max_shift, progressSignal = None):
    """
        gets optical flow of a complete imagestack, based on blockmatching
        unit is px/frame as no scale is given here yet
        blockwidth is width of square macroblock
        max_shift is maximum allowed movement
        delay in frames between images to analyze
        when the qt signal progressSignal is provided, it is used to track the progress
    """
    print("Calculating Optical Flow of imagestack by means of Blockmatching")
    starttime = time.time() #for benchmarking...

    MotionVectorsAll = []
    total_frames = imageStack.shape[0] - delay
    
    for frame, (prev_img, curr_img) in enumerate(zip(imageStack, imageStack[delay:])):
        # iterate pairwise over frames, total pairs: number_frames - delay
        
        MotionVectorsX, MotionVectorsY = BM_single(prev_img, curr_img, max_shift, blockwidth)
        MotionVectorsAll.append((MotionVectorsX, MotionVectorsY))   # this can be definitely be done nicer with numpy
        
        if progressSignal != None:
            progressSignal.emit((frame+1)/total_frames)
        
    endtime = time.time()
    print('Execution time in seconds:', (endtime - starttime))

    return np.array(MotionVectorsAll)