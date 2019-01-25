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