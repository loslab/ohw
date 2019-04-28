# -*- coding: utf-8 -*-

import pathlib # change to pathlib from Python 3.4 instead of os
import tifffile
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from scipy.signal import argrelextrema
from PyQt5.QtWidgets import QMessageBox
import datetime
from libraries import OFlowCalc, Filters, plotfunctions, helpfunctions, PeakDetection, videoreader

import moviepy.editor as mpy
from moviepy.video.io.bindings import mplfig_to_npimage

__version__ = "0.2-dev" #store in main python module?

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
       
        #store exceptions that appear
        #self.exceptions = None
        #self.isROI_OHW = False
        
        self.videometa = {}   # dict of video metadata: microns_per_pixel, fps, blackval, whiteval, 
        self.analysis_meta = {"date": datetime.datetime.now(), "version": __version__}
    
    def import_video(self, inputpath, *args, **kwargs):        
        self.rawImageStack, self.videometa = videoreader.import_video(inputpath)
        self.set_auto_results_folder()
        
    def import_video_thread(self, inputpath):
        self.thread_import_video = helpfunctions.turn_function_into_thread(self.import_video, emit_progSignal = True, inputpath = inputpath)
        return self.thread_import_video       
        
    def set_video(self, rawImageStack, videometa):
        '''
        set video data + metadata directly instead of importing whole video again
        '''
        self.rawImageStack, self.videometa = rawImageStack, videometa
        self.set_auto_results_folder()    
    
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
        #self.results_folder.mkdir(parents = True, exist_ok = True) #create folder for results        

        #store parameters which were used for the calculation of MVs
        self.analysis_meta.update({'Motion_method': method, 'MV_parameters': parameters})
        
        if method == 'BM':   
            self.rawMVs = OFlowCalc.BM_stack(self.analysisImageStack, progressSignal = progressSignal, **parameters)#adjust self.scaledImageStack...
        elif method == 'GF':
            pass
        elif method == 'LK':
            pass
        elif method == 'MM':
            # self.absMotions = ...
            pass

    def calculate_motion_thread(self, **parameters):
        self.thread_calculate_motion = helpfunctions.turn_function_into_thread(self.calculate_motion, emit_progSignal=True, **parameters)
        return self.thread_calculate_motion 
    
    def initialize_motion(self):
        '''
            calculate 2D & 1D data representations after motion determination
        '''
        
        #distinguish between MVs and motion here
        
        scalingfactor, delay = self.analysis_meta["scalingfactor"], self.analysis_meta["MV_parameters"]["delay"]
        self.unitMVs = (self.rawMVs / scalingfactor) * self.videometa["microns_per_pixel"] * (self.videometa["fps"] / delay)
        self.absMotions = np.sqrt(self.unitMVs[:,0]*self.unitMVs[:,0] + self.unitMVs[:,1]*self.unitMVs[:,1])# get absolute motions per frame        
    
        self.get_mean_absMotion()
        self.prepare_quiver_components()
        self.calc_TimeAveragedMotion()
    
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
        np.save(str(self.analysis_meta["results_folder"] / 'beating_kinetics.npy'), np.array([self.timeindex,self.mean_absMotions]))
    
    def prepare_quiver_components(self):
        '''
            sets all 0-motions to nan such that they won't be plotted in quiver plot
            creates grid of coordinates
        '''
        
        self.MV_zerofiltered = Filters.zeromotion_to_nan(self.unitMVs, copy=True)
        self.MotionX = self.MV_zerofiltered[:,0,:,:]
        self.MotionY = self.MV_zerofiltered[:,1,:,:]
        
        bw = self.analysis_meta["MV_parameters"]["blockwidth"]
        
        self.MotionCoordinatesX, self.MotionCoordinatesY = np.meshgrid(
            np.arange(bw/2, self.analysisImageStack.shape[2]-bw/2, bw)+1, 
            np.arange(bw/2, self.analysisImageStack.shape[1]-bw/2+1, bw))  #changed arange range, double check!.. inconsistency in x and y?
            
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
        plotfunctions.save_heatmap(ohw_dataset = self, savepath = savepath, singleframe=False)
    
    def save_heatmap_thread(self, singleframe):
        savepath = self.analysis_meta["results_folder"]/'heatmap_results'
        self.thread_save_heatmap = helpfunctions.turn_function_into_thread(
            plotfunctions.save_heatmap, ohw_dataset = self, savepath = savepath, singleframe=False)
        return self.thread_save_heatmap

    def save_quivervid3_thread(self, skipquivers, t_cut):
        self.thread_save_quivervid3 = helpfunctions.turn_function_into_thread(
            self.save_quivervid3, singleframe = False, skipquivers=skipquivers, t_cut=t_cut)
        return self.thread_save_quivervid3
    
    def save_quiver(self, singleframe = False, skipquivers = 1, t_cut = 0, keyword = None, subfolder = None, *args, **kwargs):
        """
            saves either the selected frame (singleframe = framenumber) or the whole heatmap video (= False)
            # adjust density of arrows by skipquivers
            # todo: add option to clip arrows
            # todo: maybe move to helpfunctions?
        """
        
        # prepare MVs... needs refactoring as it's done twice!
        scale_max = self.get_scale_maxMotion2(self.absMotions)   
        self.MV_zerofiltered = Filters.zeromotion_to_nan(self.unitMVs, copy=True)
        self.MV_cutoff = Filters.cutoffMVs(self.MV_zerofiltered, max_length = scale_max, copy=True)
        
        self.MotionX = self.MV_cutoff[:,0,:,:]
        self.MotionY = self.MV_cutoff[:,1,:,:]

        blockwidth = self.MV_parameters["blockwidth"]
     #   print('Shape of scaledImageStack:')
     #   print(self.scaledImageStack.shape[1])
     #   print(self.scaledImageStack.shape[2])
#        self.MotionCoordinatesX, self.MotionCoordinatesY = np.meshgrid(np.arange(blockwidth/2, self.scaledImageStack.shape[1], blockwidth), np.arange(blockwidth/2, self.scaledImageStack.shape[2], blockwidth))        
        self.MotionCoordinatesX, self.MotionCoordinatesY = np.meshgrid(np.arange(blockwidth/2, self.scaledImageStack.shape[2], blockwidth), np.arange(blockwidth/2, self.scaledImageStack.shape[1], blockwidth))        
           
        #prepare figure
        savefig_quivers, saveax_quivers = plt.subplots(1,1)
        #w,h = helpfunctions.get_figure_size(self.scaledImageStack[0], initial_val=12)
#        savefig_quivers.set_size_inches(w,h)
        savefig_quivers.set_size_inches(16,12)
        saveax_quivers.axis('off')   
    
        
        qslice=(slice(None,None,skipquivers),slice(None,None,skipquivers))
        distance_between_arrows = blockwidth * skipquivers
        arrowscale = 1 / (distance_between_arrows / scale_max)

        imshow_quivers = saveax_quivers.imshow(self.scaledImageStack[0], vmin = self.videometa["Blackval"], vmax = self.videometa["Whiteval"], cmap = "gray")

#        print('Size of quiver data:')
#        print(self.MotionCoordinatesX.shape)
#        print(self.MotionCoordinatesY.shape)
#        print(self.MotionX[0].shape)
#        print(self.MotionY[0].shape)
#        
        # adjust desired quiver plotstyles here!
        quiver_quivers = saveax_quivers.quiver(self.MotionCoordinatesX[qslice], self.MotionCoordinatesY[qslice], self.MotionX[0][qslice], self.MotionY[0][qslice], pivot='mid', color='r', units ="xy", scale_units = "xy", angles = "xy", scale = arrowscale,  width = 4, headwidth = 3, headlength = 5, headaxislength = 5, minshaft =1.5) #width = 4, headwidth = 2, headlength = 3

        #saveax_quivers.set_title('Motion [µm/s]', fontsize = 16, fontweight = 'bold')
        if keyword == None:
            path_quivers = self.analysis_meta["results_folder"] / "quiver_results"
        elif keyword == 'batch':
            path_quivers = subfolder / "quiver_results"
        path_quivers.mkdir(parents = True, exist_ok = True) #create folder for results
        
        if not isinstance(singleframe, bool):
            # save only specified frame

            imshow_quivers.set_data(self.scaledImageStack[singleframe])
            quiver_quivers.set_UVC(self.MotionX[singleframe][qslice], self.MotionY[singleframe][qslice])
            
            quivers_filename = str(path_quivers / ('quiver_frame' + str(singleframe) + '.png'))
            savefig_quivers.savefig(quivers_filename, bbox_inches ="tight", pad_inches = 0, dpi = 200)
        
        elif isinstance(singleframe, bool): 
        # save video
            def make_frame_mpl(t):

                frame = int(round(t*self.videometa["fps"]))
                imshow_quivers.set_data(self.scaledImageStack[frame])
                try:
                    quiver_quivers.set_UVC(self.MotionX[frame][qslice], self.MotionY[frame][qslice])
                except:
                    pass
                
                return mplfig_to_npimage(savefig_quivers) # RGB image of the figure
            
            quivers_filename = str(path_quivers / 'quivervideo.mp4')
            duration = 1/self.videometa["fps"] * self.MotionX.shape[0]
            animation = mpy.VideoClip(make_frame_mpl, duration=duration)
            
            #cut clip if desired by user
            animation_to_save = self.cut_clip(clip_full=animation, t_cut=t_cut)
            
            animation_to_save.write_videofile(quivers_filename, fps=self.videometa["fps"])

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
    
    def detect_peaks(self, ratio, number_of_neighbours):
        """
            peak detection in mean_absMotions
        """
        
        self.PeakDetection.set_data(self.timeindex,self.mean_absMotions)
        
        self.PeakDetection.detectPeaks(ratio, number_of_neighbours)
        self.PeakDetection.analyzePeaks()
        self.PeakDetection.calculateTimeIntervals()
                
    def get_peaks(self):
        return self.PeakDetection.sorted_peaks
        
    def get_peakstatistics(self):
        return self.PeakDetection.peakstatistics
        
    def get_peaktime_intervals(self):
        return self.PeakDetection.time_intervals
    
    def get_bpm(self):
        return self.PeakDetection.bpm
    
    def export_peaks(self):
        self.PeakDetection.export_peaks(self.analysis_meta["results_folder"])
    
    def exportEKG_CSV(self):
        self.PeakDetection.exportEKG_CSV(self.analysis_meta["results_folder"])
    
    def exportStatistics(self):
        self.PeakDetection.exportStatistics(self.analysis_meta)
    
    def plot_beatingKinetics(self, mark_peaks = False, filename=None, keyword=None):
        if keyword == None:
            filename = filename[0]
        if filename is None:
            filename=self.analysis_meta["results_folder"]/ 'beating_kinetics.png'
                
        plotfunctions.plot_Kinetics(self.timeindex, self.mean_absMotions, self.PeakDetection.sorted_peaks, mark_peaks, filename)
  
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
    
    def plot_TimeAveragedMotions(self, file_ext):
        plotfunctions.plot_TimeAveragedMotions(self.avg_absMotion, self.avg_MotionX, self.avg_MotionY, self.max_avgMotion, self.analysis_meta["results_folder"], file_ext)
    
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