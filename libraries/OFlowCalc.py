# -*- coding: utf-8 -*-

import cv2
import math
import numpy as np
import time
from PyQt5.QtCore import QThread, pyqtSignal

from skimage import feature, morphology
from skimage.measure import block_reduce
from scipy.ndimage import binary_fill_holes

"""
    currently offered methods for OFlow calculation (for 2 images)
    - Blockmatch (BM_single)
    - LucasKanade (LK_single)
    - GunnarFarnebäck (GF_single)
    
    for stack:
    - Blockmatch (BM_stack)

"""

def LK_single(img_prev, img_curr):
    # insert cv2 code
    pass

def BM_single(img_prev, img_curr, max_shift, blockwidth, searchblocks=None):
    """
        gets optical flow by block matching between 2 images with parameters of max_shift and blockwidth
        searchblocks = bool array with dimensions of resulting motion vector array, specifies if motion will be calculated in this block
    """

    size_ver, size_hor = img_prev.shape[:2]
    MVs_ver = math.floor(size_ver/blockwidth)   # number of MVs in horizontal direction
    MVs_hor = math.floor(size_hor/blockwidth)
    
    if type(searchblocks) != np.ndarray:
        searchblocks = np.ones((MVs_ver, MVs_hor), dtype=bool) # is done for each calculation, optimize...
    
    # pad image to enable searching at edge
    # e.g. for max_shift = 7 -> 2x7 + 1 possible shifts
    img_curr = cv2.copyMakeBorder(img_curr,max_shift,max_shift,max_shift,max_shift,cv2.BORDER_REPLICATE)
    
    #img_curr = cv2.GaussianBlur(img_curr, (15,15), 2)
    #img_prev = cv2.GaussianBlur(img_prev, (15,15), 2)
    """
    img_curr = img_curr[:,:,0] / 4095 * 255
    img_prev = img_prev[:,:,0] / 4095 * 255    
    # implement smoothing for noise reduction
    
    blur = cv2.GaussianBlur(img_prev, (7,7), 2)
    I = np.max(blur) - blur
    edges = feature.canny(I,sigma = 3, use_quantiles = True, low_threshold  = 0.2,high_threshold =0.7)
    #https://www.mathworks.com/matlabcentral/answers/458235-why-is-the-canny-edge-detection-in-matlab-different-to-opencv
    dil = morphology.dilation(edges,selem = morphology.diamond(2))
    bw_close = morphology.binary_closing(dil, selem=morphology.disk(3))
    bw_fill = binary_fill_holes(bw_close)
    cleaned = morphology.remove_small_objects(bw_fill, min_size=500, connectivity=0)
    #out = np.copy(imstack[0])
    #img_prev[~cleaned] = 0
    
    # if one component of edge(=cleaned) in searchRegion -> dont't find MV
    #edges = np.ones((MVs_ver, MVs_hor), dtype=bool)
    edge = block_reduce(cleaned, block_size=(blockwidth,blockwidth), func=np.any)[:MVs_ver,:MVs_hor] #downsample detected edge -> if any value in block = True -> calculate optical flow
    print(edge.shape,"MVs_ver,hor:",MVs_ver,MVs_hor)
    """
    
    # prepare arrays for MVs (component X & Y)
    MotionVectorsX = np.zeros(shape = (MVs_ver,MVs_hor))
    MotionVectorsY = np.zeros(shape = (MVs_ver,MVs_hor))
    
    # iterate over blocks
    for rowidx in range(MVs_ver):   # np.arange or range? use numpy/ parallelize better!
        for colidx in range(MVs_hor):
        
            #if np.any(cleaned[rowidx*blockwidth:rowidx*blockwidth+blockwidth,colidx*blockwidth:colidx*blockwidth+blockwidth]):
            if searchblocks[rowidx,colidx] == True:
                patternToFind = img_prev[rowidx*blockwidth:rowidx*blockwidth+blockwidth,colidx*blockwidth:colidx*blockwidth+blockwidth]
                searchRegion = img_curr[rowidx*blockwidth:rowidx*blockwidth+blockwidth+2*max_shift,colidx*blockwidth:colidx*blockwidth+blockwidth+2*max_shift]
                        
                MotionVectorsX[rowidx, colidx], MotionVectorsY[rowidx, colidx] = BM_getMV(patternToFind, searchRegion, max_shift)
        
            else:
                MotionVectorsX[rowidx, colidx], MotionVectorsY[rowidx, colidx] = 0,0
                
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
        
        # for matlab comparison
        min_occ = np.count_nonzero(matchResult == min_val)
        if min_occ != 1:
            #print("occurences of min. match:", min_occ, "selected location:",top_left) # for multiple occurences: does not automatically pick origin
            top_left = [max_shift,max_shift]
    else:
        top_left = max_loc    
    
    # subtract max_shift, as center (= no movement) is situated at this coordinate
    xMotion = top_left[0] - max_shift
    yMotion = top_left[1] - max_shift
    
    return xMotion, yMotion
    
def BM_stack(imageStack, blockwidth, delay, max_shift, canny = True, progressSignal = None, *args, **kwargs):
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
    
    if canny:
        print("performing Canny edge detection on first frame to select region")
        searchblocks = find_searchblocks(imageStack[0],blockwidth)
    else:
        searchblocks = None # replace with np.ones here from function BM_single...
    
    for frame, (prev_img, curr_img) in enumerate(zip(imageStack, imageStack[delay:])):
        # iterate pairwise over frames, total pairs: number_frames - delay
        
        MotionVectorsX, MotionVectorsY = BM_single(prev_img, curr_img, max_shift, blockwidth, searchblocks = searchblocks)

        MotionVectorsAll.append((MotionVectorsX, MotionVectorsY))   # this can be definitely be done nicer with numpy
        
        if progressSignal != None:
            progressSignal.emit((frame+1)/total_frames)
            
        # for comparison with matlab...
        #prev_img = prev_img[:,:,0] / 4095 * 255
        #curr_img = curr_img[:,:,0] / 4095 * 255
        #if frame < 3:
        #    print(prev_img, frame)
        #    print(MotionVectorsX, MotionVectorsY)   
        
        #    %Scale edges to macroblocks
        #for k = 0:(length(refImage(:,1))/mbSize-1)
        #    for l =0:(length(refImage(1,:))/mbSize-1)
        #         BlockValue = prod(prod(single(LocalEdges((k*mbSize)+1:(k+1)*mbSize,(l*mbSize)+1:(l+1)*mbSize))));
        #        LocalEdges((k*mbSize)+1:(k+1)*mbSize,(l*mbSize)+1:(l+1)*mbSize) = BlockValue
        #    end
        #end
        # ... simplify in python -> define all blocks in which edge lies
            
    endtime = time.time()
    print('Execution time in seconds:', (endtime - starttime))

    return np.array(MotionVectorsAll)
    
    
def find_searchblocks(inputimage, blockwidth):
    ''' 
        perform canny edge detection and binary operations 
        to define searchblocks, i.e. blocks in which to perform blockmatching
    '''

    size_ver, size_hor = inputimage.shape[:2]   # is calculated twice... optimize
    MVs_ver = math.floor(size_ver/blockwidth)   # number of MVs in horizontal direction
    MVs_hor = math.floor(size_hor/blockwidth)

    blur = cv2.GaussianBlur(inputimage, (7,7), 2)
    I = np.max(blur) - blur
    edges = feature.canny(I,sigma = 3, use_quantiles = True, low_threshold  = 0.2,high_threshold = 0.7)
    #https://www.mathworks.com/matlabcentral/answers/458235-why-is-the-canny-edge-detection-in-matlab-different-to-opencv
    dil = morphology.dilation(edges,selem = morphology.diamond(2))
    bw_close = morphology.binary_closing(dil, selem=morphology.disk(3))
    bw_fill = binary_fill_holes(bw_close)
    cleaned = morphology.remove_small_objects(bw_fill, min_size=500, connectivity=0)
    #out = np.copy(imstack[0])
    #img_prev[~cleaned] = 0
    
    # if one component of edge(=cleaned) in searchRegion -> dont't find MV
    #edges = np.ones((MVs_ver, MVs_hor), dtype=bool)
    searchblocks = block_reduce(cleaned, block_size=(blockwidth,blockwidth), func=np.any) #downsample detected edge -> if any value in block = True -> calculate optical flow
    return searchblocks[:MVs_ver,:MVs_hor] #cut off overlapping values
    
def get_mean_absMotion(absMotions):
    """
        calculates movement mask (eliminates all pixels where no movement occurs through all frames)
        applies mask to absMotions and calculate mean motion per frame
    """

    summed_absMotions = np.sum(absMotions, axis = 0)  # select only points in array with nonzero movement
    movement_mask = (summed_absMotions == 0)
    
    filtered_absMotions = np.copy(absMotions) #copy needed, don't influence absMotions
    filtered_absMotions[:,movement_mask] = np.nan
    mean_absMotions = np.nanmean(filtered_absMotions, axis=(1,2))
    
    return mean_absMotions
    
    #self.analysis_meta["results_folder"].mkdir(parents = True, exist_ok = True) #create folder for results if it doesn't exist
    #self.timeindex = (np.arange(self.mean_absMotions.shape[0]) / self.videometa["fps"]).round(2)
    
    #np.save(str(self.analysis_meta["results_folder"] / 'beating_kinetics.npy'), np.array([self.timeindex,self.mean_absMotions]))
    #save in own function if desired...