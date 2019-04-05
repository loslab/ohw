# -*- coding: utf-8 -*-

import pathlib # change to pathlib from Python 3.4 instead of os
import tifffile
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from scipy.signal import argrelextrema
from PyQt5.QtWidgets import QMessageBox
from libraries import OFlowCalc, Filters, plotfunctions, helpfunctions, PeakDetection

import moviepy.editor as mpy
from moviepy.video.io.bindings import mplfig_to_npimage

class OHW():
    """
        main class of OpenHeartWare
        bundles MVs + parameters 
    """
    def __init__(self):
        
        self.inputpath = None #
        self.rawImageStack = None       # array for raw imported imagestack
        self.ROIImageStack = None       # array for ROIs
        self.scaledImageStack = None
        self.rawMVs = None              # array for raw motion vectors (MVs)
        self.videoMeta = {"microns_per_pixel":1,"fps":1,"blackval":0,"whiteval":None}   # dict of video metadata: microns_per_pixel, fps, blackval, whiteval, 
        self.unitMVs = None             # MVs in correct unit (microns)
        self.scalingfactor = None

        self.MV_parameters = None       # dict for MV parameters
        self.results_folder = None      # folder for saving results
        self.absMotions = None
        self.mean_absMotions = None     # for 1D-representation
        self.avg_absMotion = None       # time averaged absolute motion
        self.avg_MotionX = None         # time averaged x-motion
        self.avg_MotionY = None         # time averaged y-motion
        self.max_avgMotion = None       # maximum of time averaged motions
        self.timeindex = None           # time index for 1D-representation

        self.PeakDetection = PeakDetection.PeakDetection()    # class which detects + saves peaks
       
        #store exceptions that appear
        self.exceptions = None
        self.isROI_OHW = False
        
    def read_imagestack(self, inputfolder, *args, **kwargs):
        """
            reads desired inputvideo as np.array
            choose inputmethod based on file extension
            --> populate self.rawImageStack
        """
        print("Reading images from path ", inputfolder)
        
        self.inputpath = pathlib.Path(inputfolder)
        
        if self.inputpath.is_file():
        #    print("... which is a single file")
            
            self.rawImageStack, self.videoMeta["fps"] = self.read_videofile(str(self.inputpath))
            
            dtype = self.rawImageStack[0,0,0].dtype

            
            self.videoMeta["microns_per_pixel"] = 1
            
            self.videoMeta["Blackval"], self.videoMeta["Whiteval"] = np.percentile(self.rawImageStack[0], (0.1, 99.9))

            self.results_folder = self.inputpath.parent / ("results_" + str(self.inputpath.stem) )
            
        elif self.inputpath.is_dir():
            # directory with .tifs
     #       print("... which is a folder")
            inputtifs = list(self.inputpath.glob('*.tif'))  # or use sorted instead of list
     #       print("number of tifs: {}".format(len(inputtifs)))
            
            #directory contains no .tifs: warning message and proceed
            if len(inputtifs) == 0:
               # raise Exception('.tif error')
                self.exceptions = []
                self.exceptions.append(Exception('.tif error'))
                return
            
            #directory contains .tifs:
            self.exceptions = None
            self.rawImageStack = tifffile.imread(inputtifs, pattern = "")
            self.rawImageStack = self.rawImageStack.astype(np.float32)    #convert as cv2 needs float32 for templateMatching
     #       print('Shape of rawImageStack after loading tiffs: [%d, %d, %d]' %(self.rawImageStack.shape[0], self.rawImageStack.shape[1], self.rawImageStack.shape[2]))
            self.videoMeta["Blackval"], self.videoMeta["Whiteval"] = np.percentile(self.rawImageStack[0], (0.1, 99.9))  #set default values, will be overwritten by all values in videoinfos file
            
            #get_tif_meta (from first and second image, stored in imagej tag)
            if (self.inputpath / "videoinfos.txt").is_file():
                # set metadata from file if videoinfos.txt exists
                print("videoinfos.txt exists in inputfolder, reading parameters.")
                self.get_videoinfos_file()
            
            self.results_folder = self.inputpath / "results"
        
        self.videoMeta["fps"] = round(self.videoMeta["fps"], 1)
        
        """
        # folder with imageseries (tif-only at the moment), read with tifffile
        if folder:
            if videoinfos file
                read videoinfos from file
                set non-specified values to default values (easier: set all to default and change new ones) (auto-adj. black-white)
            elif info in tiftag
                read infos from tag
                set non-specified values to default values (auto-adj. black-white)
            else 
                use default values
                auto-adj. black-white
    
        # single movie file, use cv2 as reader
        if file:
        """
    
    def read_imagestack_thread(self, inputfolder):
        self.thread_read_imagestack = helpfunctions.turn_function_into_thread(self.read_imagestack, emit_progSignal = True, inputfolder = inputfolder)
        return self.thread_read_imagestack
    
    def read_videofile(self, inputpath):
        cap = cv2.VideoCapture(inputpath)

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

        cap.release()
        return rawImageStack, videofps
    
    def get_videoinfos_file(self):
        """
            reads dict from file videoinfos.txt and sets values in videoMeta
        """
        filereader = (self.inputpath / "videoinfos.txt").open("r")
        videoinfos_file = eval(filereader.read())
        filereader.close()
        for key, value in videoinfos_file.items():
            self.videoMeta[key] = value
    
    def scale_ImageStack(self, max_size_w=1024, max_size_h=1024):
        """
            rescales input ImageStack
        """
      #  print ("rescaling images to max. size of", max_size)
     #   print("shape of raw image stack: ", self.rawImageStack.shape)
        scaledImages = []
        if self.ROIImageStack is not None:
         #   print('Use ROIImageStack for further processing.')
            for image in self.ROIImageStack:
                scaledImages.append(cv2.resize(image,(max_size_h,max_size_w)))
                
        else:
        #    print('Use rawImageStack for further processing.')
            for image in self.rawImageStack:   #rawImageStack[:-2]
                scaledImages.append(cv2.resize(image,(max_size_h,max_size_w)))
              
        self.scaledImageStack = np.array(scaledImages)
        self.scalingfactor = self.scaledImageStack[0].shape[0] / self.rawImageStack[0].shape[0]
   #     print("shape of scaled down image stack: ", self.scaledImageStack.shape)
   #     print("scalingfactor: ", self.scalingfactor)
    
    def plot_scalebar(self):
        """
            plots scalebar onto np-array
        """
        # move to other module
        sizeX = self.scaledImageStack.shape[1]
        resolution_units = self.videoMeta["microns_per_pixel"] / self.scalingfactor
        scalebar = helpfunctions.create_scalebar(sizeX,resolution_units)*(self.videoMeta["Whiteval"]/255)    #Oli
        scale_width_px = scalebar.shape[0]
        scale_height_px = scalebar.shape[1]
        self.scaledImageStack[:,-1-scale_width_px:-1,-1-scale_height_px:-1] = scalebar        
    
    def calculate_MVs_thread(self, **parameters):
        self.thread_calculate_MVs = helpfunctions.turn_function_into_thread(self.calculate_MVs, emit_progSignal=True, **parameters)
        return self.thread_calculate_MVs            
    
    def initialize_calculatedMVs(self):
        self.results_folder.mkdir(parents = True, exist_ok = True) #create folder for results
        #self.rawMVs = self.thread_BM_stack.MotionVectorsAll
       # print('in initalia_calcMVS')
        #print(self.rawMVs.shape)
        self.unitMVs = (self.rawMVs / self.scalingfactor) * self.videoMeta["microns_per_pixel"] * (self.videoMeta["fps"] / self.MV_parameters["delay"])
        self.absMotions = np.sqrt(self.unitMVs[:,0]*self.unitMVs[:,0] + self.unitMVs[:,1]*self.unitMVs[:,1])# get absolute motions per frame
    
        self.get_mean_absMotion()
        self.calc_TimeAveragedMotion()
    
    def calculate_MVs(self, method = 'BM', progressSignal = None, **parameters):
        """
            calculates motionvectors MVs of imagestack based on method and parameters
        """
    
        """
            switch method:
            
            -blockmatch
            -gunnar farnbäck
            -lucas-kanade
            
            self.rawMVs = ...
        """
        self.results_folder.mkdir(parents = True, exist_ok = True) #create folder for results        
        self.MV_parameters = parameters   #store parameters which were used for the calculation of MVs
        
        if method == 'BM':   
            self.rawMVs = OFlowCalc.BM_stack(self.scaledImageStack, progressSignal = progressSignal, **parameters)
        # these are double! also in initialize_calculatedMVs, remove from here if it does not conflict...
        self.unitMVs = (self.rawMVs / self.scalingfactor) * self.videoMeta["microns_per_pixel"] * (self.videoMeta["fps"] / self.MV_parameters["delay"])
        self.absMotions = np.sqrt(self.unitMVs[:,0]*self.unitMVs[:,0] + self.unitMVs[:,1]*self.unitMVs[:,1])# get absolute motions per frame
        
        self.get_mean_absMotion()
        self.calc_TimeAveragedMotion()
    
    def save_heatmap(self, singleframe = False, keyword = None, subfolder = None, *args, **kwargs):
        """
            saves either the selected frame (singleframe = framenumber) or the whole heatmap video (=False)
        """
        
        #prepare figure
        savefig_heatmaps, saveax_heatmaps = plt.subplots(1,1)
      #  w,h = helpfunctions.get_figure_size(self.scaledImageStack[0],initial_val=12)
      #  savefig_heatmaps.set_size_inches(w,h)
        savefig_heatmaps.set_size_inches(16,12) 
        saveax_heatmaps.axis('off')   
        
        scale_max = self.get_scale_maxMotion()
        imshow_heatmaps = saveax_heatmaps.imshow(self.absMotions[0], vmin = 0, vmax = scale_max, cmap = "jet", interpolation="bilinear")#  cmap="inferno"
        
        cbar_heatmaps = savefig_heatmaps.colorbar(imshow_heatmaps)
        cbar_heatmaps.ax.tick_params(labelsize=20)
        for l in cbar_heatmaps.ax.yaxis.get_ticklabels():
            l.set_weight("bold")
        saveax_heatmaps.set_title('Motion [µm/s]', fontsize = 16, fontweight = 'bold')
        
        if keyword == None:
            path_heatmaps = self.results_folder / "heatmap_results"
        elif keyword == 'batch':
            path_heatmaps = subfolder / "heatmap_results"
        path_heatmaps.mkdir(parents = True, exist_ok = True) #create folder for results
        
        if singleframe != False:
        # save only specified frame
            imshow_heatmaps.set_data(self.absMotions[singleframe])
            
            heatmap_filename = str(path_heatmaps / ('heatmap_frame' + str(singleframe) + '.png'))
            savefig_heatmaps.savefig(heatmap_filename,bbox_inches ="tight",pad_inches =0)
        
        else:
        # save video
            def make_frame_mpl(t):

                frame = int(round(t*self.videoMeta["fps"]))
                imshow_heatmaps.set_data(self.absMotions[frame])

                return mplfig_to_npimage(savefig_heatmaps) # RGB image of the figure
            
            heatmap_filename = str(path_heatmaps / 'heatmapvideo.mp4')
            duration = 1/self.videoMeta["fps"] * self.absMotions.shape[0]
            animation = mpy.VideoClip(make_frame_mpl, duration=duration)
         #   animation.resize((1500,800))
            animation.write_videofile(heatmap_filename, fps=self.videoMeta["fps"])    

    def save_heatmap_thread(self, singleframe):
        self.thread_save_heatmap = helpfunctions.turn_function_into_thread(self.save_heatmap, singleframe=False)
        return self.thread_save_heatmap
    
    def save_quivervid3(self, skipquivers = 1, t_cut = 0, *args, **kwargs):
        """
            saves a video with the normal beating, beating + quivers and velocity trace
        """
        
        scale_max = self.get_scale_maxMotion2()   
        self.MV_zerofiltered = Filters.zeromotion_to_nan(self.unitMVs, copy=True)
        self.MV_cutoff = Filters.cutoffMVs(self.MV_zerofiltered, max_length = scale_max, copy=True)
        
        self.MotionX = self.MV_cutoff[:,0,:,:]
        self.MotionY = self.MV_cutoff[:,1,:,:]

        blockwidth = self.MV_parameters["blockwidth"]
        self.MotionCoordinatesX, self.MotionCoordinatesY = np.meshgrid(np.arange(blockwidth/2, self.scaledImageStack.shape[1], blockwidth), np.arange(blockwidth/2, self.scaledImageStack.shape[2], blockwidth))        
           
        #prepare figure
        outputfigure = plt.figure(figsize=(14,10), dpi = 150)#figsize=(6.5,12)

        gs = gridspec.GridSpec(3,2, figure=outputfigure)
       # add_gridspec(3, 2)
        gs.tight_layout(outputfigure)
        plt.tight_layout()
        
        saveax_video = outputfigure.add_subplot(gs[0:2, 0])
        saveax_video.axis('off')        
        
        saveax_quivers = outputfigure.add_subplot(gs[0:2, 1])
        saveax_quivers.axis('off')

        saveax_trace = outputfigure.add_subplot(gs[2,:])
        saveax_trace.plot(self.timeindex, self.mean_absMotions, '-', linewidth = 2)
        
        saveax_trace.set_xlim(left = 0, right = self.timeindex[-1])
        saveax_trace.set_ylim(bottom = 0)
        saveax_trace.set_xlabel('t [s]', fontsize = 22)
        saveax_trace.set_ylabel(u'$\mathrm{\overline {v}}$ [\xb5m/s]', fontsize = 22)
        saveax_trace.tick_params(labelsize = 20)

        for side in ['top','right','bottom','left']:
            saveax_trace.spines[side].set_linewidth(2) 
        
        self.marker, = saveax_trace.plot(self.timeindex[0],self.mean_absMotions[0],'ro')
        
        #savefig_quivers, saveax_quivers = plt.subplots(1,1)
        #savefig_quivers.set_size_inches(8, 10)
        #saveax_quivers.axis('off')   
    
        ###### prepare video axis
        imshow_video = saveax_video.imshow(self.scaledImageStack[0], vmin = self.videoMeta["Blackval"], vmax = self.videoMeta["Whiteval"], cmap = "gray")
        
        qslice=(slice(None,None,skipquivers),slice(None,None,skipquivers))
        distance_between_arrows = blockwidth * skipquivers
        arrowscale = 1 / (distance_between_arrows / scale_max)
               
        imshow_quivers = saveax_quivers.imshow(self.scaledImageStack[0], vmin = self.videoMeta["Blackval"], vmax = self.videoMeta["Whiteval"], cmap = "gray")
        # adjust desired quiver plotstyles here!
        quiver_quivers = saveax_quivers.quiver(self.MotionCoordinatesX[qslice], self.MotionCoordinatesY[qslice], self.MotionX[0][qslice], self.MotionY[0][qslice], pivot='mid', color='r', units ="xy", scale_units = "xy", angles = "xy", scale = arrowscale,  width = 4, headwidth = 3, headlength = 5, headaxislength = 5, minshaft =1.5) #width = 4, headwidth = 2, headlength = 3
        #saveax_quivers.set_title('Motion [µm/s]', fontsize = 16, fontweight = 'bold')

        path_quivers = self.results_folder / "quiver_results"
        path_quivers.mkdir(parents = True, exist_ok = True) #create folder for results

        # parameters for cropping white border in output video
        sizex, sizey = outputfigure.get_size_inches()*outputfigure.dpi
        bbox = outputfigure.get_tightbbox(outputfigure.canvas.get_renderer())
        bbox_bounds_px = np.round(np.asarray(bbox.extents*outputfigure.dpi)).astype(int)

        # to do: introduce min/max to be on the safe side!
        # reverse for np indexing
        bbox_bounds_px[3] = sizey - bbox_bounds_px[1]#y1
        bbox_bounds_px[1] = sizey - bbox_bounds_px[3]#y0

        bbox_bounds_px[2] = sizex - bbox_bounds_px[0]#x1
        bbox_bounds_px[0] = sizex - bbox_bounds_px[2]#x0
        
        # save video
        def make_frame_mpl(t):

            frame = int(round(t*self.videoMeta["fps"]))
            imshow_quivers.set_data(self.scaledImageStack[frame])
            imshow_video.set_data(self.scaledImageStack[frame])
            quiver_quivers.set_UVC(self.MotionX[frame][qslice], self.MotionY[frame][qslice])
            
            self.marker.remove()
            self.marker, = saveax_trace.plot(self.timeindex[frame],self.mean_absMotions[frame],'ro')
            self.marker.set_clip_on(False)
            
            return mplfig_to_npimage(outputfigure)[bbox_bounds_px[1]:bbox_bounds_px[3],bbox_bounds_px[0]:bbox_bounds_px[2]] # RGB image of the figure  #150:1450,100:1950
            # slicing here really hacky! find better solution!
            # find equivalent to bbox_inches='tight' in savefig
            # mplfig_to_npimage just uses barer canvas.tostring_rgb()
            # -> check how bbox_inches works under the hood
            # -> in print_figure:
            # if bbox_inches:
            # call adjust_bbox to save only the given area
        
        quivers_filename = str(path_quivers / 'quivervideo3.mp4')
        duration = 1/self.videoMeta["fps"] * self.MotionX.shape[0]
        animation = mpy.VideoClip(make_frame_mpl, duration=duration)
        
        #cut clip if desired by user
        animation_to_save = self.cut_clip(clip_full=animation, t_cut=t_cut)
       
        animation_to_save.write_videofile(quivers_filename, fps=self.videoMeta["fps"])
            
        print("frames:", self.MotionX.shape[0], "1/fps:", 1/self.videoMeta["fps"])
        outputfigure.savefig(str(path_quivers / 'lastquiver3.png'))
    
    def save_quivervid3_thread(self, skipquivers, t_cut):
        self.thread_save_quivervid3 = helpfunctions.turn_function_into_thread(self.save_quivervid3, skipquivers=skipquivers, t_cut=t_cut)
        return self.thread_save_quivervid3
    
    def save_quiver(self, singleframe = False, skipquivers = 1, t_cut = 0, keyword = None, subfolder = None, *args, **kwargs):
        """
            saves either the selected frame (singleframe = framenumber) or the whole heatmap video (= False)
            # adjust density of arrows by skipquivers
            # todo: add option to clip arrows
            # todo: maybe move to helpfunctions?
        """
        
        # prepare MVs... needs refactoring as it's done twice!
        scale_max = self.get_scale_maxMotion2()   
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

        imshow_quivers = saveax_quivers.imshow(self.scaledImageStack[0], vmin = self.videoMeta["Blackval"], vmax = self.videoMeta["Whiteval"], cmap = "gray")

        print('Size of quiver data:')
        print(self.MotionCoordinatesX.shape)
        print(self.MotionCoordinatesY.shape)
        print(self.MotionX[0].shape)
        print(self.MotionY[0].shape)
        
        # adjust desired quiver plotstyles here!
        quiver_quivers = saveax_quivers.quiver(self.MotionCoordinatesX[qslice], self.MotionCoordinatesY[qslice], self.MotionX[0][qslice], self.MotionY[0][qslice], pivot='mid', color='r', units ="xy", scale_units = "xy", angles = "xy", scale = arrowscale,  width = 4, headwidth = 3, headlength = 5, headaxislength = 5, minshaft =1.5) #width = 4, headwidth = 2, headlength = 3

        #saveax_quivers.set_title('Motion [µm/s]', fontsize = 16, fontweight = 'bold')
        if keyword == None:
            path_quivers = self.results_folder / "quiver_results"
        elif keyword == 'batch':
            path_quivers = subfolder / "quiver_results"
        path_quivers.mkdir(parents = True, exist_ok = True) #create folder for results
        
        if singleframe != False:
            # save only specified frame

            imshow_quivers.set_data(self.scaledImageStack[singleframe])
            quiver_quivers.set_UVC(self.MotionX[singleframe][qslice], self.MotionY[singleframe][qslice])
            
            quivers_filename = str(path_quivers / ('quiver_frame' + str(singleframe) + '.png'))
            savefig_quivers.savefig(quivers_filename, bbox_inches ="tight", pad_inches = 0, dpi = 200)
        
        else:
        # save video
            def make_frame_mpl(t):

                frame = int(round(t*self.videoMeta["fps"]))
                imshow_quivers.set_data(self.scaledImageStack[frame])
                quiver_quivers.set_UVC(self.MotionX[frame][qslice], self.MotionY[frame][qslice])

                return mplfig_to_npimage(savefig_quivers) # RGB image of the figure
            
            quivers_filename = str(path_quivers / 'quivervideo.mp4')
            duration = 1/self.videoMeta["fps"] * self.MotionX.shape[0]
            animation = mpy.VideoClip(make_frame_mpl, duration=duration)
            
            #cut clip if desired by user
            animation_to_save = self.cut_clip(clip_full=animation, t_cut=t_cut)
            
            animation_to_save.write_videofile(quivers_filename, fps=self.videoMeta["fps"])

    def save_quiver_thread(self, singleframe, skipquivers, t_cut):
        self.thread_save_quiver = helpfunctions.turn_function_into_thread(self.save_quiver, singleframe=False, skipquivers=skipquivers, t_cut=t_cut)
        return self.thread_save_quiver
            
    def cut_clip(self, clip_full, t_cut=0):
        #if user chose to cut the clip after t_cut seconds:
        t_cut = round(t_cut, 2)
        
        if t_cut is not 0:
            print('t_cut is of type:')
            print(t_cut)
            print(type(t_cut))
            #t_cut is the end of the clip in seconds of the original clip
            return clip_full.subclip(t_start=0, t_end=t_cut)
        
        else:
            return clip_full
    
    def save_MVs(self):
        """
            saves raw MVs as npy file
        """
        save_file = str(self.results_folder / 'rawMVs.npy')
        np.save(save_file, self.rawMVs)   #MotionVectorsAll
        save_file_units = str(self.results_folder / 'unitMVs.npy')
        np.save(save_file_units, self.unitMVs)
    
    def get_mean_absMotion(self):
        """
            calculates movement mask (eliminates all pixels where no movement occurs through all frames)
            applies mask to absMotions and calculate mean motion per frame
        """
        # move into filter module in future?
        summed_absMotions = np.sum(self.absMotions, axis = 0)  # select only points in array with nonzero movement
        movement_mask = summed_absMotions == 0
        
        filtered_absMotions = np.copy(self.absMotions)
        filtered_absMotions[:,movement_mask] = np.nan
        self.mean_absMotions = np.nanmean(filtered_absMotions, axis=(1,2))
        self.timeindex = (np.arange(self.mean_absMotions.shape[0]) / self.videoMeta["fps"]).round(2)
        np.save(str(self.results_folder / 'beating_kinetics.npy'),np.array([self.timeindex,self.mean_absMotions]))
    
    def get_scale_maxMotion(self):
        """
            returns maximum for scaling of heatmap + arrows in quiver
        """
        
        max_motion_framenr = np.argmax(self.mean_absMotions)
        max_motion_frame = self.absMotions[max_motion_framenr]
        scale_min, scale_maxMotion = np.percentile(max_motion_frame, (0.1, 95))
        return scale_maxMotion
    
    def get_scale_maxMotion2(self):
        """
            returns maximum for scaling of heatmap + arrows in quiver
            v2: takes all frames into account, select positions where motion > 0, max represents 80th percentile
        """
        
        #absMotions = np.sqrt(self.unitMVs[:,0]*self.unitMVs[:,0] + self.unitMVs[:,1]*self.unitMVs[:,1])
        absMotions_flat = self.absMotions[self.absMotions>0].flatten()
        scale_min, scale_maxMotion = np.percentile(absMotions_flat, (0, 80))   
        return scale_maxMotion
    
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
        self.PeakDetection.export_peaks(self.results_folder)
    
    def exportEKG_CSV(self):
        self.PeakDetection.exportEKG_CSV(self.results_folder)
    
    def exportStatistics(self):
        self.PeakDetection.exportStatistics(self.results_folder, self.inputpath, self.MV_parameters["blockwidth"], self.MV_parameters["delay"], self.videoMeta["fps"], self.MV_parameters["max_shift"], self.scalingfactor)#results_folder, inputpath, blockwidth, delay, fps, maxShift, scalingfactor):
    
    def plot_beatingKinetics(self, mark_peaks = False, filename=None, keyword=None):
        if keyword == None:
            filename = filename[0]
        if filename is None:
            filename=self.results_folder + 'beating_kinetics.png'
                
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

        self.max_avgMotion = np.max ([self.avg_absMotion, self.avg_MotionX, self.avg_MotionY])    
    
    def plot_TimeAveragedMotions(self, file_ext):
        plotfunctions.plot_TimeAveragedMotions(self.avg_absMotion, self.avg_MotionX, self.avg_MotionY, self.max_avgMotion, self.results_folder, file_ext)
    
    def createROIImageStack(self, r):
        #r are coordinates of rectangular that was selected as ROI
        print(r)
        self.ROIImageStack = []
        for idx in range(0, self.rawImageStack.shape[0]):
            image_ROI = self.rawImageStack[idx][int(r[1]):int(r[1]+r[3]), int(r[0]):int(r[0]+r[2])]
            self.ROIImageStack.append(image_ROI)
        self.ROIImageStack = np.asarray(self.ROIImageStack)
      #  self.ROIImageStack = [img[int(r[1]):int(r[1]+r[3]), int(r[0]):int(r[0]+r[2])] for img in self.rawImageStack.tolist()]
      #  self.ROIImageStack = np.asarray(self.ROIImageStack)
            
if __name__ == "__main__":
    OHW = OHW()
    #OHW.read_imagestack("..//sampleinput")
    #OHW.read_imagestack("..//sampleinput//samplemov.mov")
#    OHW.read_imagestack("..//sampleinput//sampleavi.avi")
#    OHW.scale_ImageStack()
#    OHW.calculate_MVs(blockwidth = 16, delay = 2, max_shift = 7)