# -*- coding: utf-8 -*-

import numpy as np
from libraries import OFlowCalc, plotfunctions, Filters, helpfunctions, PeakDetection

class Postproc():
    """
        postprocessor class
        continues analysis of calculated motion, e.g. enables selection of a specific roi
        or specific filters and subsequent motion calculation
    """
    # depending on analysis there can be various MVs/variables to store/track
    # TODO: decide what happens if cohw = None
    
    def __init__(self, cohw, name=None):
        self.filters = {"filter_singlemov":{"on":False, "par": "parval"}}
        self.roi = None
        self.PeakDetection = PeakDetection.PeakDetection()    # class which detects + saves peaks
        
        if name is None:
            name = "default"
        self.set_name(name)
        
        self.link_ohw(cohw)
        
        # link to config somehow/ default pars somehow
        # init somewhere else?

    def link_ohw(self, cohw):
        """ connect to ohw analysis object cohw (current ohw) with calculated motion and other metadata """
        # or does it make sense to do this already in the constructor?
        self.cohw = cohw
        
        #check if analysis already happened before connecting?
        
    def set_name(self, name):
        """ specify name of specific Postproc operation, like tissue_spot1 or mybestfilterset """
        self.name = name
        
    def set_roi(self, roi = None):
        """ sets roi of postprocessing region. If a list of roi coordinates is provided use list, otherwise open selection"""
        if roi is None:
            
            roi = self.cohw.analysis_meta["roi"] # works only if roi != None
            #print("analysis roi", roi)
            roi = [int(coord*self.cohw.videometa["prev_scale"]) for coord in roi] # scale to 800 px coord
            #print("analysis roi in 800 px", roi)
            analysis_img = self.cohw.videometa["prev800px"][int(roi[1]):int(roi[1]+roi[3]), int(roi[0]):int(roi[0]+roi[2])]
            self.roi = helpfunctions.sel_roi(analysis_img) #roi has to be rescaled now to analysis_img
            self.roi = [int(coord/self.cohw.videometa["prev_scale"]) for coord in self.roi] # scale to orig coord
            
            # works so far...
            # roi = roi of analysis
            # self.roi = selected subroi of analysis crop in orig coord.... quite confusing

        elif isinstance(roi, list):
            self.roi = roi
    
        # TODO: check if roi boundaries are allowed...
    
    def reset_roi(self):
        self.roi = None
    
    def process(self):
        """ starts postprocessing, i.e. selects subset of MVs and performs filterng """
        # basically same as init_motion previously did
        # ... to be seen to what extent quiver components or similarly should be calculated here
        
        scalingfactor, delay = self.cohw.analysis_meta["scalingfactor"], self.cohw.analysis_meta["MV_parameters"]["delay"]
        bw = self.cohw.analysis_meta["MV_parameters"]['blockwidth']
        
        # select MVs of calculation (possibly done in a roi of inputvid) by subroi:
        
        if self.roi is None:
            rawMVs_filt = self.cohw.rawMVs[:,:,:,:]
        else:
            roi = self.roi
            # scale roi to adjusted imagestack resolution used for calculation
            roi = [int(coord*scalingfactor) for coord in roi] 
            
            MVslice_x, MVslice_y = get_slice_from_roi(roi,bw)
            #print("orig shape:",  self.cohw.rawMVs.shape)
            rawMVs_filt = self.cohw.rawMVs[:,:,MVslice_x, MVslice_y] 
        
        #print("selected shape:",rawMVs_filt.shape)
        #print("slices", MVslice_x, MVslice_y)

        #for filter in self.filters:
        if self.filters["filter_singlemov"]["on"] == True:
            rawMVs_filt = Filters.filter_singlemov(rawMVs_filt)
            
        self.unitMVs = (rawMVs_filt / scalingfactor) * self.cohw.videometa["microns_per_px"] * (self.cohw.videometa["fps"] / delay)
        self.absMotions = np.sqrt(self.unitMVs[:,0]*self.unitMVs[:,0] + self.unitMVs[:,1]*self.unitMVs[:,1])# get absolute motions per frame
        
        #print("absMotions shape: ", self.absMotions.shape)
        
        self.mean_absMotions = OFlowCalc.get_mean_absMotion(self.absMotions)
        self.timeindex = (np.arange(self.mean_absMotions.shape[0]) / self.cohw.videometa["fps"]).round(2)
        
        self.prepare_quiver_components()
        self.calc_TimeAveragedMotion()
        self.PeakDetection.set_data(self.timeindex, self.mean_absMotions) #or pass self directly?
        
        # when to create results folder?
        #self.analysis_meta["results_folder"].mkdir(parents = True, exist_ok = True) #create folder for results if it doesn't exist
        #plotfunctions.plot_Kinetics(timeindex, mean_absMotions, None, None, None, file_name=None)
    
    def set_filter(self, filtername = "", on = True, **filterparameters):
        """ turns specific filter on/ off and sets specified parameters to filter """
        if filtername in self.filters:
            self.filters[filtername]["on"] = on
            self.filters[filtername].update(filterparameters)
        else:
            print("filter {} is not a valid filteroption".format(filtername))
    
    # might be best to turn filters in future in class (derived from general filter class)?
    # only rudimental filter implementation so far
    
    def get_processpar(self):
        """ shows all filters and parameters"""
        print("set roi: ", self.roi)
        
        print("set filter options:")
        for filtername, filterdict in self.filters.items():
            print("filter \"" + filtername + " with parameters: ")
            print (filterdict)
    
    
    # add flag to track if processing already took place
    # allow export, save + reimport of parameters + rois (also detected peaks)
    
    def get_peaks(self):
        return self.PeakDetection.Peaks, self.PeakDetection.hipeaks, self.PeakDetection.lopeaks
    
    def prepare_quiver_components(self):
        '''
            sets all 0-motions to nan such that they won't be plotted in quiver plot
            determines scale_max and cuts off all longer vectors
            creates grid of coordinates
        '''
        
        MV_zerofiltered = Filters.zeromotion_to_nan(self.unitMVs, copy=True)
        scale_max = helpfunctions.get_scale_maxMotion2(self.absMotions)        
        MV_cutoff = Filters.cutoffMVs(MV_zerofiltered, max_length = scale_max) #copy=True
        
        self.QuiverMotionX = MV_cutoff[:,0,:,:] # changed name to QuiverMotionX as values are manipulated here
        self.QuiverMotionY = MV_cutoff[:,1,:,:]
        
        bw = self.cohw.analysis_meta["MV_parameters"]["blockwidth"]
        Nx, Ny = MV_cutoff[0,0].shape
        
        self.MotionCoordinatesX, self.MotionCoordinatesY = np.meshgrid(
            np.arange(Ny)*bw+bw/2,
            np.arange(Nx)*bw+bw/2) #Nx, Ny exchanged (np vs. image indexing); possible issues with odd bws?
            
    def calc_TimeAveragedMotion(self):
        ''' calculates time averaged motion for abs. motion, x- and y-motion '''
        
        self.avg_absMotion = np.nanmean(self.absMotions, axis = 0)
        MotionX = self.unitMVs[:,0,:,:]
        MotionY = self.unitMVs[:,1,:,:]    #squeeze not necessary anymore, dimension reduced
        
        absMotionX = np.abs(MotionX)    #calculate mean of absolute values!
        self.avg_MotionX = np.nanmean(absMotionX, axis = 0)

        absMotionY = np.abs(MotionY)
        self.avg_MotionY = np.nanmean(absMotionY, axis = 0)

        self.max_avgMotion = np.max ([self.avg_absMotion, self.avg_MotionX, self.avg_MotionY]) # avg_absMotion should be enough