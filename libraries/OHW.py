# -*- coding: utf-8 -*-

import pathlib # change to pathlib from Python 3.4 instead of os
import tifffile, cv2, datetime, pickle
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from libraries import OFlowCalc, Filters, plotfunctions, helpfunctions, PeakDetection, videoreader, postproc

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
        self.rawMVs = None              # array for raw motion vectors (MVs)
        self.unitMVs = None             # MVs in correct unit (microns)
        
        # bundle these parameters in dict?
        self.avg_absMotion = None       # time averaged absolute motion
        self.avg_MotionX = None         # time averaged x-motion
        self.avg_MotionY = None         # time averaged y-motion
        self.max_avgMotion = None       # maximum of time averaged motions

        self.postprocs = {"post1":postproc.Postproc(cohw=self, name="post1")} # rename to evals?
        self.set_ceval("post1")
        
        self.video_loaded = False       # tells state if video is connected to ohw-objecet
        self.config = helpfunctions.read_config() # load current config
        
        self.raw_videometa = {"inputpath":""} # raw info after importing  # dict of video metadata: microns_per_px, fps, blackval, whiteval,
        self.set_default_videometa(self.raw_videometa)
        self.videometa = self.raw_videometa.copy()
        self.analysis_meta = {"date": datetime.datetime.now(), "version": self.config['UPDATE']['version'], 
            "calc_finish":False, "has_MVs": False, "results_folder":"", "roi":None}
        self.init_kinplot_options()

    def reset(self):
        """ resets instance to default values """
        pass
    
    def import_video(self, inputpath, *args, **kwargs):        
        self.rawImageStack, self.raw_videometa = videoreader.import_video(inputpath)
        self.set_default_videometa(self.raw_videometa)
        self.videometa = self.raw_videometa.copy()
        self.set_auto_results_folder()
        self.video_loaded = True
        self.videometa["prev800px"] = helpfunctions.create_prev(self.rawImageStack[0], 800)
        self.videometa["prev_scale"] = 800/self.videometa["frameHeight"]
        
    def import_video_thread(self, inputpath):
        self.thread_import_video = helpfunctions.turn_function_into_thread(self.import_video, emit_progSignal = True, inputpath = inputpath)
        return self.thread_import_video       
        
    def reload_video(self, *args, **kwargs):
        """
            reloads video, analysis file is norally opened without loading the video to save time
            -> reload if video display or videoexport desired
        """
        inputpath = self.videometa["inputpath"]
        self.rawImageStack, self.raw_videometa = videoreader.import_video(inputpath)
        self.set_analysisImageStack(px_longest = self.analysis_meta["px_longest"]) #roi automatically considered      
        self.video_loaded = True

    def reload_video_thread(self):
        self.thread_reload_video = helpfunctions.turn_function_into_thread(self.reload_video, emit_progSignal = True)
        return self.thread_reload_video  
    
    def set_default_videometa(self, videometa):
        """
            gets default values from config if not found in input
            rounds values to specified digits
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
         
    def set_analysisImageStack(self, px_longest = None):
        '''
            specifies resolution + roi of video to be analyzed
            px_longest: resolution of longest side
            if px_longest = None: original resolution is used
            roi: specify region of interest, coordinates of rectangular that was selected as ROI in unmodified coordinates
            if no special roi is given, the roi saved in analysis_meta is used
        '''
        
        self.analysis_meta.update({'px_longest': px_longest, "scalingfactor":1})
        
        self.analysisImageStack = self.rawImageStack
        # select roi
        roi = self.analysis_meta["roi"]
        if roi != None:
            self.analysisImageStack = self.analysisImageStack[:,int(roi[1]):int(roi[1]+roi[3]), int(roi[0]):int(roi[0]+roi[2])]

        # rescale input
        # take original resoltuion if no other specified
        if px_longest != None:
            self.analysisImageStack, self.analysis_meta["scalingfactor"] = helpfunctions.scale_ImageStack(self.analysisImageStack, px_longest=px_longest)
        self.analysis_meta.update({'shape': self.analysisImageStack.shape})

    def save_ohw(self):
        '''
            saves ohw analysis object with all necessary info
            especially useful after batchrun
            -> no need to recalculate MVs when filters/ plotting parameters are changed
        '''
        if self.analysis_meta["results_folder"] == "": # don't save when no file loaded
            return
        filename = str(self.analysis_meta["results_folder"]/'ohw_analysis.pickle')
        
        # get savedata for all current postprocs:
        postproc_savedict = {name: eval.get_savedata() for name, eval in self.postprocs.items()}
        
        savedata = {"analysis_meta":self.analysis_meta, "videometa":self.videometa,
                    "postproc_savedict":postproc_savedict, "kinplot_options":self.kinplot_options,
                    "rawMVs":self.rawMVs} #leave kinplot_options here?
        #savedata = [self.analysis_meta, self.videometa, self.rawMVs, self.PeakDetection.Peaks] 
        #savedata = [self.analysis_meta, self.videometa, postproc_savedict, self.kinplot_options] #leave kinplot_options here?
        
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
        
        # implement reset method to reset instance
        self.reset()
        
        with open(filename, 'rb') as loadfile:
            data = pickle.load(loadfile)
        
        #return data
        print(data)

        self.analysis_meta = data["analysis_meta"]
        self.videometa = data["videometa"]
        loaded_postprocs = data["postproc_savedict"]
        self.kinplot_options = data["kinplot_options"]
        
        if "rawMVs" in data.keys():
            self.rawMVs = data["rawMVs"]
        
        #, self.videometa, loaded_postprocs, self.kinplot_options = data
        
        self.postprocs = {}
        for name, loaded_postproc in loaded_postprocs.items():
            eval = postproc.Postproc(cohw=self, name=name)
            eval.load_data(loaded_postproc)
            
            self.postprocs.update({name:eval})

        self.ceval = self.postprocs[list(self.postprocs.keys())[0]] #set one as active
        
        """
        #print(self.analysis_meta)
        
        self.video_loaded = False
        self.init_motion()
        self.set_peaks(Peaks) #call after init_motion as this resets peaks
        """


    def set_method(self, method, parameters):
        self.analysis_meta.update({'Motion_method': method, 'MV_parameters': parameters})

    def get_method(self):
        return self.analysis_meta["Motion_method"]

    def calculate_motion(self, method = 'Blockmatch', progressSignal = None, overwrite = False, **parameters):
        """
            calculates motion (either motionvectors MVs or absolute motion) of imagestack based 
            on specified method and parameters

            allowed methods:
            -Blockmatch (BM)
            -GF: gunnar farnbäck
            -LK: lucas-kanade
            -MM: musclemotion
        """

        if (overwrite == False) and (self.analysis_meta["calc_finish"] == True):
            print("motion already calculated, don't overwrite")
            return False
        
        #store parameters which will be used for the calculation of MVs
        self.set_method(method, parameters)
        
        if method == 'Blockmatch':   
            self.rawMVs = OFlowCalc.BM_stack(self.analysisImageStack, 
                progressSignal = progressSignal, **parameters)
            self.analysis_meta["has_MVs"], self.analysis_meta["calc_finish"] = True, True #calc_finish: new variable to track state -> lock to prevent overwriting
            self.kinplot_options.update({"vmin":0})

        elif method == 'Fluo-Intensity':
            # as mean intensity can be calculated on the fly, no extra calculation needed here
            self.analysis_meta["has_MVs"], self.analysis_meta["calc_finish"] = False, True
            self.kinplot_options.update({"vmin":None})

        else:
            print("method ", method, " currently not supported.")
        
        """
        elif method == 'GF':
            pass
        elif method == 'LK':
            pass
        elif method == 'MM':
            # self.absMotions = ...
            pass
        """

    def calculate_motion_thread(self, **parameters):
        self.thread_calculate_motion = helpfunctions.turn_function_into_thread(
            self.calculate_motion, emit_progSignal=True, **parameters)
        return self.thread_calculate_motion 
    
    def set_filter(self, filtername, on = False, **filterparameters):
        ''' sets specified filtername on/ off + parameters '''
        # TODO: better error handling if filter does not exist (what's the best way?)
        self.ceval.set_filter(filtername, on, **filterparameters)
    
    def get_filter(self):
        ''' gets filterdict from current eval/postproc'''
        return self.ceval.get_filter()
    
    def set_ceval(self, eval_name):
        '''
            sets active postprocess/ current evaluation for use in viewing/ interaction
            active postprocess = ceval (current evaluation) with name ceval_name
        '''
        # TODO: check if name exists in postproc dict
        
        self.ceval_name = eval_name # rename ceval_name to sth shorter!
        self.ceval = self.postprocs[self.ceval_name]
    
    def init_motion(self):
        '''
            calculate 2D & 1D data representations after motion determination
            2D: motionvectors (MVs)
            1D: motion (calculated from MVs or other attributes...)
        '''
        
        # perform evaluation on currently active postprocess/evaluation
        self.ceval.process()
    
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

    def save_heatmap(self, singleframe):
        savepath = self.analysis_meta["results_folder"]/'heatmap_results'
        plotfunctions.save_heatmap(ohw_dataset = self, savepath = savepath, singleframe=singleframe)
    
    def save_heatmap_thread(self, singleframe):
        savepath = self.analysis_meta["results_folder"]/'heatmap_results'
        self.thread_save_heatmap = helpfunctions.turn_function_into_thread(
            plotfunctions.save_heatmap, ohw_dataset = self, savepath = savepath, singleframe=False)
        return self.thread_save_heatmap

    def save_quiver3(self, singleframe, skipquivers = 1):
        savepath = self.analysis_meta["results_folder"]/'quiver_results'
        plotfunctions.save_quiver3(ohw_dataset = self, savepath = savepath, singleframe=singleframe, skipquivers=skipquivers)
    
    def save_quiver3_thread(self, singleframe, skipquivers):#t_cut
        savepath = self.analysis_meta["results_folder"]/'quiver_results'
        self.thread_save_quiver3 = helpfunctions.turn_function_into_thread(
            plotfunctions.save_quiver3, ohw_dataset = self, savepath = savepath, singleframe = singleframe, skipquivers=skipquivers)#t_cut=t_cut
        return self.thread_save_quiver3

    def save_quiver_thread(self, singleframe, skipquivers, t_cut):
        self.thread_save_quiver = helpfunctions.turn_function_into_thread(self.save_quiver, singleframe=False, skipquivers=skipquivers, t_cut=t_cut)
        return self.thread_save_quiver
    
    def set_peaks(self, Peaks):
        ''' update with manually added/ deleted peaks '''
        self.ceval.set_peaks(Peaks)
    
    def detect_peaks(self, ratio, number_of_neighbours):
        ''' automated peak detection in mean_absMotions'''
        self.ceval.detect_peaks(ratio, number_of_neighbours)
       
    def get_peaks(self):
        return self.ceval.get_peaks()
        
    def get_peakstatistics(self):
        return self.ceval.get_peakstatistics()
    
    def export_analysis(self):
        self.ceval.export_analysis()
    
    def plot_kinetics(self, filename=None):
        if filename == None:
            filename=self.analysis_meta["results_folder"]/ 'beating_kinetics.png'
        self.ceval.plot_kinetics(filename)

    def init_kinplot_options(self):
        self.kinplot_options = dict(self.config._sections['KINPLOT OPTIONS'])
        for key, value in self.kinplot_options.items(): # can be definitely improved...
            if value == "None":
                self.kinplot_options[key] = None
            elif value == "true":
                self.kinplot_options[key] = True
            elif value == "false":
                self.kinplot_options[key] = False
            else:
                self.kinplot_options[key] = float(value)
        self.kinplot_options.update({"tmin":0})
        
    def update_kinplot_options(self, kinplot_options):
        self.kinplot_options.update(kinplot_options)
        #also change config to new value?
    
    def plot_TimeAveragedMotions(self, file_ext='.png'):
        plotfunctions.plot_TimeAveragedMotions(self, file_ext)

    def selROI(self, roi = None):
        """
            if no roi is specified:
            opens a cv2 window which allows the selection of a roi of the currently loaded video
            roi is always specified in coordinates of original video resolution
        """
        if self.video_loaded == False:
            print("no video loaded, can't select a ROI")
            return False
        
        if roi is None:
            sel_roi = helpfunctions.sel_roi(self.videometa["prev800px"]) # select roi in 800 px preview img
            sel_roi = [int(coord/self.videometa["prev_scale"]) for coord in sel_roi] # rescale to coord in orig inputdata
            self.analysis_meta["roi"] = sel_roi
            print("selected roi:", sel_roi)
            return True
        
        if isinstance(roi, list):
            self.analysis_meta["roi"] = roi
            print("manually setting roi to", roi)
            # use these coordinates as roi
            return True

    def resetROI(self):
        if self.video_loaded == False:
            print("no video loaded, can't reset ROI")
            return False
        self.analysis_meta["roi"] = None
            
if __name__ == "__main__":
    OHW = OHW()