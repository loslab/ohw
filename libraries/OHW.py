# -*- coding: utf-8 -*-

import pathlib # change to pathlib from Python 3.4 instead of os
import tifffile, cv2, datetime, pickle
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from libraries import OFlowCalc, Filters, plotfunctions, helpfunctions, PeakDetection, videoreader

import moviepy.editor as mpy
from moviepy.video.io.bindings import mplfig_to_npimage

class OHW():
    """
        main class of OpenHeartWare
        bundles analysis (algorithm + parameters + ROI + MVs)
        --> in future: can be saved to reuse
    """
    def __init__(self):
        
        self.rawImageStack = None       # array for raw imported imagestack
        #self.ROIImageStack = None      # array for ROIs
        self.rawMVs = None              # array for raw motion vectors (MVs)
        self.unitMVs = None             # MVs in correct unit (microns)

        #self.MV_parameters = None       # dict for MV parameters
        
        # bundle these parameters in dict?
        self.absMotions = None          # absolulte motions, either from MVs or from intensity
        self.mean_absMotions = None     # for 1D-representation
        self.avg_absMotion = None       # time averaged absolute motion
        self.avg_MotionX = None         # time averaged x-motion
        self.avg_MotionY = None         # time averaged y-motion
        self.max_avgMotion = None       # maximum of time averaged motions
        self.timeindex = None           # time index for 1D-representation

        self.PeakDetection = PeakDetection.PeakDetection()    # class which detects + saves peaks
        self.video_loaded = False       # tells state if video is connected to ohw-objecet
       
        #self.exceptions = None
        #self.isROI_OHW = False
        self.config = helpfunctions.read_config() # load current config
        
        self.raw_videometa = {} # raw info after importing  # dict of video metadata: microns_per_px, fps, blackval, whiteval,
        self.videometa = {}
        self.analysis_meta = {"date": datetime.datetime.now(), "version": self.config['UPDATE']['version'], 
            "motion_calculated":False, "has_MVs": False}
        self.init_kinplot_options()
    
    def import_video(self, inputpath, *args, **kwargs):        
        self.rawImageStack, self.raw_videometa = videoreader.import_video(inputpath)
        self.set_default_videometa(self.raw_videometa)
        self.videometa = self.raw_videometa.copy()
        self.set_auto_results_folder()
        self.video_loaded = True
        
    def import_video_thread(self, inputpath):
        self.thread_import_video = helpfunctions.turn_function_into_thread(self.import_video, emit_progSignal = True, inputpath = inputpath)
        return self.thread_import_video       
        
    def reload_video(self, *args, **kwargs):
        inputpath = self.videometa["inputpath"]
        self.rawImageStack, self.raw_videometa = videoreader.import_video(inputpath)
        self.video_loaded = True

    def reload_video_thread(self):
        self.thread_reload_video = helpfunctions.turn_function_into_thread(self.reload_video, emit_progSignal = True)
        return self.thread_reload_video  
    
    def set_default_videometa(self, videometa):
        """
            gets default values from config if not found in input
        """
        for key in ["fps","microns_per_px"]:
            if key not in videometa.keys():
                videometa[key] = self.config['DEFAULT VALUES'][key]
        videometa["fps"] = round(float(videometa["fps"]), 1)# round fps to 1 digit
        videometa["microns_per_px"] = round(float(videometa["microns_per_px"]), 4)
    
    def set_video(self, rawImageStack, videometa):
        '''
        set video data + metadata directly instead of importing whole video again
        '''
        self.rawImageStack, self.videometa = rawImageStack, videometa
        self.raw_videometa = self.videometa.copy() #raw_videometa not available anymore
        self.set_auto_results_folder()
        self.video_loaded = True
    
    def set_auto_results_folder(self):
        # set results folder
        inputpath = self.videometa["inputpath"]        
        if self.videometa["input_type"] == 'videofile':
            self.analysis_meta["results_folder"] = inputpath.parent / ("results_" + str(inputpath.stem) )
        else:
            self.analysis_meta["results_folder"] = inputpath.parent / "results"
        self.analysis_meta["inputpath"] = inputpath
         
    def set_analysisImageStack(self, px_longest = None, roi = None):
        '''
            specifies resolution + roi of video to be analyzed
            px_longest: resolution of longest side
            if px_longest = None: original resolution is used
            roi: specify region of interest, coordinates of rectangular that was selected as ROI in unmodified coordinates
        '''
        
        self.analysis_meta.update({'px_longest': px_longest, 'roi': roi, "scalingfactor":1})
        
        self.analysisImageStack = self.rawImageStack
        # select roi
        if roi != None:
            self.analysisImageStack = self.analysisImageStack[:,int(roi[1]):int(roi[1]+roi[3]), int(roi[0]):int(roi[0]+roi[2])]
            pass
        
        # rescale input
        # take original resoltuion if no other specified
        if px_longest != None:
            self.analysisImageStack, self.analysis_meta["scalingfactor"] = helpfunctions.scale_ImageStack(self.analysisImageStack, px_longest=px_longest)
        
        self.analysis_meta.update({'shape': self.analysisImageStack.shape})

    def save_ohw(self):
        """
            saves ohw analysis object with all necessary info
            -> no need to recalculate MVs when filters/ plotting parameters are changed
            especially useful after batchrun
        """
        filename = str(self.analysis_meta["results_folder"]/'ohw_analysis.pickle')
        savedata = [self.analysis_meta, self.videometa, self.rawMVs] 
        # keep saving minimal, everything should be reconstructed from these parameters...

        self.analysis_meta["results_folder"].mkdir(parents = True, exist_ok = True)
        with open(filename, 'wb') as writefile:
            pickle.dump(savedata, writefile, protocol=pickle.HIGHEST_PROTOCOL)

    def load_ohw(self, filename):
        """
            loads ohw analysis object saved previously and sets corresponding variables
            initializes motion to get to the same state before saving
        """
        # take care if sth will be overwritten?
        # best way to insert rawImageStack?
        
        with open(filename, 'rb') as loadfile:
            data = pickle.load(loadfile)
        self.analysis_meta, self.videometa, self.rawMVs = data
        self.video_loaded = False
        self.init_motion()

    def calculate_motion(self, method = 'BM', progressSignal = None, **parameters):
        """
            calculates motion (either motionvectors MVs or absolute motion) of imagestack based 
            on specified method and parameters

            allowed methods:
            -BM: blockmatch
            -GF: gunnar farnbäck
            -LK: lucas-kanade
            -MM: musclemotion
        """

        #store parameters which wwill be used for the calculation of MVs
        self.analysis_meta.update({'Motion_method': method, 'MV_parameters': parameters})
        
        if method == 'BM':   
            self.rawMVs = OFlowCalc.BM_stack(self.analysisImageStack, 
                progressSignal = progressSignal, **parameters)
            self.analysis_meta["has_MVs"], self.analysis_meta["motion_calculated"] = True, True

        elif method == 'GF':
            pass
        elif method == 'LK':
            pass
        elif method == 'MM':
            # self.absMotions = ...
            pass

    def calculate_motion_thread(self, **parameters):
        self.thread_calculate_motion = helpfunctions.turn_function_into_thread(
            self.calculate_motion, emit_progSignal=True, **parameters)
        return self.thread_calculate_motion 
    
    def init_motion(self):
        '''
            calculate 2D & 1D data representations after motion determination
        '''
        
        #distinguish between MVs and motion here
        
        scalingfactor, delay = self.analysis_meta["scalingfactor"], self.analysis_meta["MV_parameters"]["delay"]
        self.unitMVs = (self.rawMVs / scalingfactor) * self.videometa["microns_per_px"] * (self.videometa["fps"] / delay)
        self.absMotions = np.sqrt(self.unitMVs[:,0]*self.unitMVs[:,0] + self.unitMVs[:,1]*self.unitMVs[:,1])# get absolute motions per frame        
    
        self.get_mean_absMotion()
        self.prepare_quiver_components()
        self.calc_TimeAveragedMotion()
        self.PeakDetection.set_data(self.timeindex, self.mean_absMotions) #or pass self directly?
    
    def get_mean_absMotion(self):
        """
            calculates movement mask (eliminates all pixels where no movement occurs through all frames)
            applies mask to absMotions and calculate mean motion per frame
        """
        # move into filter module in future?
        summed_absMotions = np.sum(self.absMotions, axis = 0)  # select only points in array with nonzero movement
        movement_mask = (summed_absMotions == 0)
        
        filtered_absMotions = np.copy(self.absMotions) #copy needed, don't influence absMotions
        filtered_absMotions[:,movement_mask] = np.nan
        self.mean_absMotions = np.nanmean(filtered_absMotions, axis=(1,2))
        
        self.analysis_meta["results_folder"].mkdir(parents = True, exist_ok = True) #create folder for results if it doesn't exist
        self.timeindex = (np.arange(self.mean_absMotions.shape[0]) / self.videometa["fps"]).round(2)
        #np.save(str(self.analysis_meta["results_folder"] / 'beating_kinetics.npy'), np.array([self.timeindex,self.mean_absMotions]))
        #save in own function if desired...
        
    def prepare_quiver_components(self):
        '''
            sets all 0-motions to nan such that they won't be plotted in quiver plot
            determines scale_max and cuts off all longer vectors
            creates grid of coordinates
        '''
        
        self.MV_zerofiltered = Filters.zeromotion_to_nan(self.unitMVs, copy=True)
        scale_max = helpfunctions.get_scale_maxMotion2(self.absMotions)        
        MV_cutoff = Filters.cutoffMVs(self.MV_zerofiltered, max_length = scale_max) #copy=True
        
        self.QuiverMotionX = MV_cutoff[:,0,:,:] # changed name to QuiverMotionX as values are manipulated here
        self.QuiverMotionY = MV_cutoff[:,1,:,:]
        
        bw = self.analysis_meta["MV_parameters"]["blockwidth"]
        Nx, Ny = MV_cutoff[0,0].shape
        
        self.MotionCoordinatesX, self.MotionCoordinatesY = np.meshgrid(
            np.arange(Ny)*bw+bw/2,
            np.arange(Nx)*bw+bw/2) #Nx, Ny exchanged (np vs. image indexing); possible issues with odd bws?
            
    def save_MVs(self):
        """
            saves raw MVs as npy file
            ... replace with functions which pickles all data in class?
        """
        results_folder = self.analysis_meta["results_folder"]
        results_folder.mkdir(parents = True, exist_ok = True) #create folder for results if it doesn't exist
        
        save_file = str(results_folder / 'rawMVs.npy')
        np.save(save_file, self.rawMVs)
        save_file_units = str(results_folder / 'unitMVs.npy')
        np.save(save_file_units, self.unitMVs)            

    #def plot_scalebar(self):
    # moved to module: helpfunctions.insert_scalebar(imageStack, videometa, analysis_meta)

    def save_heatmap(self, singleframe):
        savepath = self.analysis_meta["results_folder"]/'heatmap_results'
        plotfunctions.save_heatmap(ohw_dataset = self, savepath = savepath, singleframe=singleframe)
    
    def save_heatmap_thread(self, singleframe):
        savepath = self.analysis_meta["results_folder"]/'heatmap_results'
        self.thread_save_heatmap = helpfunctions.turn_function_into_thread(
            plotfunctions.save_heatmap, ohw_dataset = self, savepath = savepath, singleframe=False)
        return self.thread_save_heatmap

    def save_quiver3(self, singleframe):
        savepath = self.analysis_meta["results_folder"]/'quiver_results'
        plotfunctions.save_quiver3(ohw_dataset = self, savepath = savepath, singleframe=singleframe)
    
    def save_quiver3_thread(self, singleframe, skipquivers):#t_cut
        savepath = self.analysis_meta["results_folder"]/'quiver_results'
        self.thread_save_quiver3 = helpfunctions.turn_function_into_thread(
            plotfunctions.save_quiver3, ohw_dataset = self, savepath = savepath, singleframe = singleframe, skipquivers=skipquivers)#t_cut=t_cut
        return self.thread_save_quiver3

    def save_quiver_thread(self, singleframe, skipquivers, t_cut):
        self.thread_save_quiver = helpfunctions.turn_function_into_thread(self.save_quiver, singleframe=False, skipquivers=skipquivers, t_cut=t_cut)
        return self.thread_save_quiver
            
    def cut_clip(self, clip_full, t_cut=0):
        #if user chose to cut the clip after t_cut seconds:
        t_cut = round(t_cut, 2)
        
        if t_cut is not 0:
            #t_cut is the end of the clip in seconds of the original clip
            return clip_full.subclip(t_start=0, t_end=t_cut)
        
        else:
            return clip_full
    
    def set_peaks(self, Peaks):
        ''' update with manually added/ deleted peaks '''
        self.PeakDetection.set_peaks(Peaks)
        self.order_peaks()
    
    def detect_peaks(self, ratio, number_of_neighbours):
        ''' automated peak detection in mean_absMotions'''

        self.PeakDetection.detect_peaks(ratio, number_of_neighbours)
        self.order_peaks()
    
    def order_peaks(self):
        self.PeakDetection.order_peaks()
                
    def get_peaks(self):
        return self.PeakDetection.Peaks, self.PeakDetection.hipeaks, self.PeakDetection.lopeaks
        
    def get_peakstatistics(self):
        self.PeakDetection.calc_peakstatistics()
        return self.PeakDetection.get_peakstatistics()
    
    def export_analysis(self):
        self.PeakDetection.export_analysis(self.analysis_meta["results_folder"])
    
    def plot_beatingKinetics(self, filename=None):
        if filename == None:
            filename=self.analysis_meta["results_folder"]/ 'beating_kinetics.png'
        plotfunctions.plot_Kinetics(self.timeindex, self.mean_absMotions, self.kinplot_options, 
                self.PeakDetection.hipeaks, self.PeakDetection.lopeaks, filename)

    def init_kinplot_options(self):
        self.kinplot_options = dict(self.config._sections['KINPLOT OPTIONS'])
        self.kinplot_options["mark_peaks"] = True #to do: add this to config and allow to be changed in gui
        for key, value in self.kinplot_options.items():
            if value == "None":
                self.kinplot_options[key] = None
            else:
                self.kinplot_options[key] = float(value)
        
    def set_kinplot_options(self, kinplot_options):
        self.kinplot_options = kinplot_options
        #also change config to new value?

    def calc_TimeAveragedMotion(self):
        """
            calculates time averaged motion for abs. motion x- and y-motion
        """
        
        self.avg_absMotion = np.nanmean(self.absMotions, axis = 0)
        MotionX = self.unitMVs[:,0,:,:]
        MotionY = self.unitMVs[:,1,:,:]    #squeeze not necessary anymore, dimension reduced
        
        absMotionX = np.abs(MotionX)    #calculate mean of absolute values!
        self.avg_MotionX = np.nanmean(absMotionX, axis = 0)

        absMotionY = np.abs(MotionY)
        self.avg_MotionY = np.nanmean(absMotionY, axis = 0)

        self.max_avgMotion = np.max ([self.avg_absMotion, self.avg_MotionX, self.avg_MotionY]) # avg_absMotion should be enough
    
    def plot_TimeAveragedMotions(self, file_ext='.png'):
        plotfunctions.plot_TimeAveragedMotions(self, file_ext)
    
    def createROIImageStack(self, r):
        #r are coordinates of rectangular that was selected as ROI
   #     print(r)
        self.ROIImageStack = []
        for idx in range(0, self.rawImageStack.shape[0]):
            image_ROI = self.rawImageStack[idx][int(r[1]):int(r[1]+r[3]), int(r[0]):int(r[0]+r[2])]
            self.ROIImageStack.append(image_ROI)
        self.ROIImageStack = np.asarray(self.ROIImageStack)
      #  self.ROIImageStack = [img[int(r[1]):int(r[1]+r[3]), int(r[0]):int(r[0]+r[2])] for img in self.rawImageStack.tolist()]
      #  self.ROIImageStack = np.asarray(self.ROIImageStack)
            
if __name__ == "__main__":
    OHW = OHW()