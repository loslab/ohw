# -*- coding: utf-8 -*-
import numpy as np

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
    """
        sets length all MVs larger than a certain value to specific value
    """
    
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