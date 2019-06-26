# -*- coding: utf-8 -*-
import numpy as np
import cv2

def zeromotion_to_nan(MotionVectors, copy = False):
    """
    filterfunction to eliminate zero-motion
    take care: function changes MotionVectors!
    """
    no_movement_mask = (MotionVectors[:,0] == 0) & (MotionVectors[:,1] == 0)
    
    if copy:  
        MotionVectorsFiltered = np.copy(MotionVectors)
    else:
        MotionVectorsFiltered = MotionVectors
    MotionVectorsFiltered[:,0][no_movement_mask] = np.nan
    MotionVectorsFiltered[:,1][no_movement_mask] = np.nan
    
    return MotionVectorsFiltered
    
def cutoffMVs(MotionVectors, max_length, copy = False):
    ''' sets length of all MVs larger than max_length to max_length '''
    
    if copy:  
        MotionVectorsFiltered = np.copy(MotionVectors)
    else:
        MotionVectorsFiltered = MotionVectors
    
    absMVs = np.sqrt(MotionVectorsFiltered[:,0]*MotionVectorsFiltered[:,0]+MotionVectorsFiltered[:,1]*MotionVectorsFiltered[:,1])
    mask = absMVs > max_length
    maskscale = absMVs[mask] / max_length
    
    MotionVectorsFiltered[:,0][mask] = MotionVectorsFiltered[:,0][mask] / maskscale
    MotionVectorsFiltered[:,1][mask] = MotionVectorsFiltered[:,1][mask] / maskscale

    return MotionVectorsFiltered

def filter_singlemov(MVs, copy = True):
    ''' filter MVs by binary erosion + dilation to remove single moving spots'''
    
    if copy:  
        MVs_filt = np.copy(MVs)
    else:
        MVs_filt = MVs
    
    Amp = np.sqrt(MVs[:,0]**2 + MVs[:,1]**2)
    filter_frames = np.zeros(Amp.shape,dtype=bool) #4D arr with filtering for each frame
    move = Amp > 0 #select spots with movement
    move = move.astype(np.uint8) #for cv2
    kernel = np.ones((2,2), np.uint8)
    
    for framenr, frame in enumerate(move):
        eroded = cv2.erode(frame,kernel)
        dilated = cv2.dilate(eroded, kernel)
        filter_frames[framenr] = dilated.astype(bool)
    filter_mask = np.any(filter_frames, axis=0) # select regions with any movement over time
    
    #filter_mask = np.broadcast_to(filter_mask, MVs.shape)
    #return MVs[:,:,filter_mask] # will return flattened array, as boolean mask only selects values
    #MVs_filt[:,:,~filter_mask] = 0 
    MVs_filt = np.where(filter_mask,MVs,0) # easier version, all nonmasked values will be replaced by 0
    # ... zeromotion_to_nan can be modified the same way
    return MVs_filt