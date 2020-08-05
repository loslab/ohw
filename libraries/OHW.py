# -*- coding: utf-8 -*-

import pathlib # change to pathlib from Python 3.4 instead of os
import tifffile, cv2, datetime, pickle
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from libraries import OFlowCalc, Filters, plotfunctions, helpfunctions, PeakDetection, videoreader, postproc
from functools import wraps
import copy

def create_analysis():
    """ creates instance of OHW class (= analysis)
    """
    cohw = OHW()
    
    return cohw

def load_analysis(picklefile):
    """ returns saved analysis (.pickle) as OHW instance
    """
    cohw = OHW()
    cohw.load_ohw(picklefile)

    return cohw

def check_finish(function, *args, **kwargs):
    """ decorator checks if calculation already finished before analysis parameters can be set/ changed
    """
    @wraps(function) #needed to keep original docstring
    def check_function(self, *args, **kwargs): #TODO: possibly introduce overwrite arg here to prevent checking?
        if self.analysis_meta["calc_finish"] == False:
            function(self, *args, **kwargs)
        else:
            print("Calculation already finished, operation not allowed. Reset analysis first.")
            return False
            
    return check_function

def batch(videofiles, param={}, stop_flag = None, progressSignal = None, *args, **kwargs):
    """
        batch processing of list of videos (= videofiles) with selected parameters
        ... if executed as thread, stop_flag provides a threading.Event() which stops the analysis
    """
    
    defaultparam = {"scaling":True, "global_resultsfolder":None, "canny":True,
                   "autoPeak":True, "heatmaps":False, "quivers":False,
                   "blockwidth":16, "delay": 2, "max_shift": 7}
    defaultparam.update(param)
    param = defaultparam
    print("running batch analysis with parameter", param)
    
    if stop_flag == None:
        stop_flag = threading.Event() #create default event if none provided
    
    for filenr, file in enumerate(videofiles):   
        if stop_flag.is_set():  break
        if progressSignal != None:
            progressSignal.emit({"filenr":filenr,"state":'load'})            
        
        print("analyzing file", file)
        filepath = pathlib.Path(file)
        curr_analysis = create_analysis()
        curr_analysis.import_video(filepath)
        curr_analysis.set_scale(2) # 1 px = microns 
        # todo: connect to param dict
        
        if param["scaling"]:
            curr_analysis.set_px_longest(px_longest=1024) # raises error if roi = None, todo: fix
            
        # adjust each results folder if option selected
        if param["global_resultsfolder"] != None:
            #print("change resultsfolder to...",self.param["global_resultsfolder"])
            inputpath = curr_analysis.videometa["inputpath"]
            results_folder = param["global_resultsfolder"]/("results_" + str(inputpath.stem) )
            curr_analysis.set_results_folder(results_folder)
            print("resultsfolder:", curr_analysis.analysis_meta["results_folder"])
        
        if param["canny"] == True:
            curr_analysis.set_prefilter("Canny",on = True)

        if stop_flag.is_set():  break
        if progressSignal != None:
            progressSignal.emit({"filenr":filenr,"state":'mcalc'})            
        #curr_analysis.calculate_motion(method = 'Blockmatch', blockwidth = 16, delay = 2, max_shift = 7, overwrite=True)
        curr_analysis.calculate_motion(method = 'Blockmatch', **param)
        curr_analysis.save_ohw()        
        # init motion not needed anymore?

        if stop_flag.is_set():  break        
        if param["autoPeak"]:
            curr_analysis.detect_peaks(0.3, 4)  #take care, values hardcoded here so far!
            curr_analysis.plot_kinetics() # chooses default path
            curr_analysis.get_peakstatistics()
            curr_analysis.export_analysis()
            curr_analysis.save_ohw() # save again as peak information is added

        if stop_flag.is_set():  break
        if progressSignal != None:
            progressSignal.emit({"filenr":filenr,"state":'heatmapvideo'})                  
        if param["heatmaps"]:
            #self.set_state(filenr,'heatmapvideo')
            curr_analysis.save_heatmap(singleframe = False)

        if stop_flag.is_set():  break
        if progressSignal != None:
            progressSignal.emit({"filenr":filenr,"state":'quivervideo'})            
        if param["quivers"]:
            #self.set_state(filenr,'quivervideo')
            curr_analysis.save_quiver3(singleframe = False, skipquivers = 4) #allow to choose between quiver and quiver3 in future  

def batch_thread(videofiles, param):
    """ returns QThread where batch runs, prevents blocking
        # todo: maybe it's smarter to directly design it as class, subclassed from thread
    """
    thread_batch = helpfunctions.turn_function_into_thread(batch, emit_progSignal = True, use_stop_flag=True, videofiles = videofiles, param = param)
    return thread_batch

'''
class CheckDecorators():
    """ class for decorators
    """

    @classmethod
    def check_finish(function, *args, **kwargs):
        """ decorator checks if calculation already finished before analysis parameters can be set/ changed
        """
        def check_function(self, *args, **kwargs):
            if self.analysis_meta["calc_finish"] == False:
                function(self, *args, **kwargs)
            else:
                print("Calculation already finished, operation not allowed. Reset analysis first.")
                return False
                
        return check_function
'''    

class OHW():
    """
        main class of OpenHeartWare  
        bundles analysis (algorithm + parameters + ROI + MVs)  
        analysis can be saved to reuse  
    """
    
    # docstring: add two trailing spaces to each line to keep whitespace in pdoc documentation
    # https://stackoverflow.com/questions/32704176/how-do-i-make-pdoc-preserve-whitespace
    
    def __init__(self):
        
        self.config = helpfunctions.read_config() # load current ohw config        
        self._init_analysis()

    def _init_analysis(self):
        """ called on instantiation to init ohw """
    
        self.rawImageStack = None       # array for raw imported imagestack
        self.rawMVs = None              # array for raw motion vectors (MVs)

        self.postprocs = {"post1":postproc.Postproc(cohw=self, name="post1")} # rename to evals?
        self.set_ceval("post1")
        self.video_loaded = False       # tells state if video is connected to ohw-objecet        

        default_prefilters = {"Canny":{"on":False}} # add options/ parameters here
        self.analysis_meta = {"date": datetime.datetime.now(), "version": self.config['UPDATE']['version'], 
            "calc_finish":False, "has_MVs": False, "results_folder":"", "roi":None, "scalingfactor":1.,
            "px_longest":None, "prefilters":default_prefilters}
            
        self.raw_videometa = {"inputpath":""} # raw info after importing  # dict of video metadata: microns_per_px, fps, blackval, whiteval,
        self.set_default_videometa(self.raw_videometa)
        self.videometa = self.raw_videometa.copy() #TODO: sketchy, refactor            
            
        self._init_kinplot_options()
        
    def reset(self):
        """ resets calculation, keeps videofile loaded -> changing of parameters allowed again """

        self.analysis_meta.update({"date": datetime.datetime.now(), "has_MVs": False, "calc_finish": False,
            "motion_method":None, "motion_parameters":None})
        #TODO: what about shape? currently not saved anymore
        self.rawMVs = None              # array for raw motion vectors (MVs), TODO: change for generic results?
        self.postprocs = {"post1":postproc.Postproc(cohw=self, name="post1")} # rename to evals?
        self.set_ceval("post1")        
    
    @check_finish
    def import_video(self, inputpath, *args, **kwargs):
        """ reads in video to current analysis  
            sets rawImageStack, videometa, prev800px and the resultsfolder
        """
        self.rawImageStack, self.raw_videometa = videoreader.import_video(inputpath)
        self.set_default_videometa(self.raw_videometa)
        self.videometa = self.raw_videometa.copy()
        self.set_auto_results_folder()
        self.video_loaded = True
        self.videometa["prev800px"] = helpfunctions.create_prev(self.rawImageStack[0], 800)
        self.videometa["prev_scale"] = 800/self.videometa["frameHeight"]
        self.reset_roi() # sets roi to video extent
        
    def import_video_thread(self, inputpath):
        """ returns QThread where import_video runs, prevents blocking
        """
        self.thread_import_video = helpfunctions.turn_function_into_thread(self.import_video, emit_progSignal = True, inputpath = inputpath)
        return self.thread_import_video       
        
    def reload_video(self, *args, **kwargs):
        """
            reloads video, analysis file is norally opened without loading the video to save time
            -> reload if video display or videoexport desired
        """
        inputpath = self.videometa["inputpath"]
        self.rawImageStack, self.raw_videometa = videoreader.import_video(inputpath)
        #self.set_analysisImageStack(px_longest = self.analysis_meta["px_longest"]) #roi automatically considered      
        self._calc_analysisStack()
        self.video_loaded = True

    def reload_video_thread(self):
        """ returns QThread where reload_video runs, prevents blocking
        """
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
        """ 
            sets results folder depending on videoinput:  
            - video -> output in videopath, foldername: results_videoname  
            - folder -> output in folder, foldername: results
        """
        # set results folder
        inputpath = self.videometa["inputpath"]        
        if self.videometa["input_type"] == 'videofile':
            self.analysis_meta["results_folder"] = inputpath.parent / ("results_" + str(inputpath.stem) )
        else:
            self.analysis_meta["results_folder"] = inputpath.parent / "results"
        self.analysis_meta["inputpath"] = inputpath

    def set_results_folder(self, results_folder):
        """ sets results folder, should be pathlib.Path """
        self.analysis_meta["results_folder"] = results_folder

    @check_finish
    def set_scale(self, mpp):
        """ 
            specify resolution of input videofile in microns per px  
            e.g. 2 microns per px -> 1 px equals 2 microns
        """
        self.videometa["microns_per_px"] = float(mpp)
    
    @check_finish
    def set_fps(self, fps):
        """
            specify framerate of input video file
        """
        self.videometa["fps"] = float(fps)
        
    @check_finish
    def set_px_longest(self, px_longest):
        """ 
            sets longest side of analysis image stack (used for scaling down + speeding up)  
            if px_longest = None: original resolution is used
        """
        self.analysis_meta["px_longest"] = px_longest
        self._calc_scalingfactor()
        
    def _calc_scalingfactor(self):
        """ calculate scalingfactor which is based on roi and px_longest
        """
        
        if self.analysis_meta["px_longest"] != None:
            roi = self.analysis_meta["roi"] #TODO: make sure roi dimensions are constrained <= image dimensions
            longest_side = max(roi[2],roi[3])
            self.analysis_meta["scalingfactor"] = float(self.analysis_meta["px_longest"])/longest_side
    
    def _calc_analysisStack(self):

        ''' selects roi + scales down input video for analysis to specified roi/ scaling
        '''
        
        self.analysisImageStack = self.rawImageStack
        
        # select roi of input ImageStack
        roi = self.analysis_meta["roi"]
        if roi != None:
            self.analysisImageStack = self.analysisImageStack[:,int(roi[1]):int(roi[1]+roi[3]), int(roi[0]):int(roi[0]+roi[2])]

        # rescale input
        # take original resoltuion if no other specified
        scalingfactor = self.analysis_meta["scalingfactor"]
        if scalingfactor != 1:
            self.analysisImageStack = helpfunctions.scale_ImageStack(self.analysisImageStack, scalingfactor)
        #self.analysis_meta.update({'shape': self.analysisImageStack.shape})

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
            correct initialization not assured yet, should be called on a new ohw instance
        """
        # take care if sth will be overwritten?
        # so far called only by top-level function on new ohw object 
        #TODO: check possible improvements
        # best way to insert rawImageStack?
        
        
        with open(filename, 'rb') as loadfile:
            data = pickle.load(loadfile)
        
        #return data
        #print(data)

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

    def _set_method(self, method, parameters):
        """ set analysis method + parameters, used before starting analysis
        """
        self.analysis_meta.update({'motion_method': method, 'motion_parameters': copy.deepcopy(parameters)})

    def get_method(self):
        """ returns method which was used for analysis
        """
        return self.analysis_meta["motion_method"]

    @check_finish #overwrite option will not work anymore
    def calculate_motion(self, method = 'Blockmatch', progressSignal = None, overwrite = False, **parameters):
        """
            calculates motion (either motionvectors MVs or absolute motion) of imagestack based 
            on specified method and parameters

            allowed methods:  
            - Blockmatch  
            - Fluo-Intensity  
            (in future:)  
            - GF: gunnar farnbäck  
            - LK: lucas-kanade  
        """

        if (overwrite == False) and (self.analysis_meta["calc_finish"] == True):
            print("motion already calculated, don't overwrite")
            return False
            
        if method not in ['Blockmatch', 'Fluo-Intensity']:
            print("method ", method, " currently not supported.")
            return False
        
        self._calc_analysisStack()
        #store parameters which will be used for the calculation of MVs
        self._set_method(method, parameters)
        
        if method == 'Blockmatch':
            
            # active canny prefilter -> get searchblocks from first frame
            if self.analysis_meta['prefilters']['Canny']['on'] == True: # quite ugly? TODO: refactor
                searchblocks  = OFlowCalc.find_searchblocks(self.analysisImageStack[0], parameters["blockwidth"])
                parameters['searchblocks'] = searchblocks #pass to BM_stack as argument
        
            self.rawMVs = OFlowCalc.BM_stack(self.analysisImageStack, 
                progressSignal = progressSignal, **parameters)
            self.analysis_meta["has_MVs"], self.analysis_meta["calc_finish"] = True, True #calc_finish: new variable to track state -> lock to prevent overwriting
            self.kinplot_options.update({"vmin":0})

        elif method == 'Fluo-Intensity':
            # as mean intensity can be calculated on the fly, no extra calculation needed here
            self.analysis_meta["has_MVs"], self.analysis_meta["calc_finish"] = False, True
            self.kinplot_options.update({"vmin":None})
            
        # perform evaluation on currently active postprocess/evaluation
        # on initial calculation 1 postprocess is automatically created
        self.ceval.process()
            
        
        """
        elif method == 'GF':
            pass
        elif method == 'LK':
            pass
        """

    def calculate_motion_thread(self, **parameters):
        """ runs calculate_motion as a QThread to prevent blocking
        passes progresssignal to track calculation progress
        """
    
        self.thread_calculate_motion = helpfunctions.turn_function_into_thread(
            self.calculate_motion, emit_progSignal=True, **parameters)
        return self.thread_calculate_motion 
    
    def set_prefilter(self, filtername, on = False, **filterparameters):
        """ 
            for filtering before analysis:  
            sets specified filtername on/ off + specifies parameters
        """
        prefilters = self.analysis_meta["prefilters"]
        if filtername in prefilters:
            prefilters[filtername]["on"] = on
            prefilters[filtername].update(filterparameters)
        else:
            print("filter {} is not a valid filteroption for prefiltering".format(filtername))
    
    
    def set_filter(self, filtername, on = False, **filterparameters):
        ''' sets specified filtername on/ off + parameters for current eval'''
        # TODO: better error handling if filter does not exist (what's the best way?)
        self.ceval.set_filter(filtername, on, **filterparameters)
    
    def get_filter(self):
        ''' gets filterdict from current eval/postproc'''
        return self.ceval.get_filter()
    
    def list_evals(self):
        """ display all postprocesses/ evaluations """

        print(list(self.postprocs.keys()))
    
    def set_ceval(self, eval_name):
        '''
            sets active postprocess/ current evaluation for use in viewing/ interaction
            active postprocess = ceval (current evaluation) with name ceval_name
        '''
        # TODO: check if name exists in postproc dict
        
        self.ceval_name = eval_name # rename ceval_name to sth shorter!
        self.ceval = self.postprocs[self.ceval_name]

    
    def save_MVs(self):
        """
            saves raw MVs as npy file
            ... replace with functions which pickles all data in class?
        """
        
        #TODO: adjust to new postprocessing interface
        results_folder = self.analysis_meta["results_folder"]
        results_folder.mkdir(parents = True, exist_ok = True) #create folder for results if it doesn't exist
        
        save_file = str(results_folder / 'rawMVs.npy')
        np.save(save_file, self.rawMVs)
        save_file_units = str(results_folder / 'unitMVs.npy')
        np.save(save_file_units, self.unitMVs)            

    def save_heatmap(self, singleframe):
        """
            saves heatmap of current evaluation  
            - of specific frame if singleframe=framenumber specified  
            - of whole video otherwise
        """
        savepath = self.analysis_meta["results_folder"]/'heatmap_results'
        plotfunctions.save_heatmap(cohw = self, savepath = savepath, singleframe=singleframe)
    
    def save_heatmap_thread(self, singleframe):
        savepath = self.analysis_meta["results_folder"]/'heatmap_results'
        self.thread_save_heatmap = helpfunctions.turn_function_into_thread(
            plotfunctions.save_heatmap, cohw = self, savepath = savepath, singleframe=False)
        return self.thread_save_heatmap

    def save_quiver3(self, singleframe, skipquivers = 1):
        savepath = self.analysis_meta["results_folder"]/'quiver_results'
        plotfunctions.save_quiver3(cohw = self, savepath = savepath, singleframe=singleframe, skipquivers=skipquivers)
    
    def save_quiver3_thread(self, singleframe, skipquivers):#t_cut
        savepath = self.analysis_meta["results_folder"]/'quiver_results'
        self.thread_save_quiver3 = helpfunctions.turn_function_into_thread(
            plotfunctions.save_quiver3, cohw = self, savepath = savepath, singleframe = singleframe, skipquivers=skipquivers)#t_cut=t_cut
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
        """ returns peaks from active evaluation """
        return self.ceval.get_peaks()
        
    def get_peakstatistics(self):
        """ returns peakstatistics from active evaluation
        """
        return self.ceval.get_peakstatistics()
    
    def export_analysis(self):
        """ exports analysis of peakstatistics of active evaluation
        """
        self.ceval.export_analysis()
    
    def plot_kinetics(self, filename=None):
        """ plots 1d motion representation of active evaluation """
        if filename == None:
            filename=self.analysis_meta["results_folder"]/ 'beating_kinetics.png'
        filename.parent.mkdir(parents = True, exist_ok = True)
        self.ceval.plot_kinetics(filename)

    def _init_kinplot_options(self):
        """ set kinplot_options to default parameters """
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
    
    def plot_TimeAveragedMotion(self, file_ext='.png'):
        """ plots time averaged motion for active eval 
        """
        #TODO: check if analysis method can be plotted this way
        self.ceval.plot_TimeAveragedMotion(file_ext='.png')

    @check_finish
    def set_roi(self, roi = None):
        """
            specify roi for analysis  
            either specify coordinates in orig video resolution  
            roi = [xstart, ystart, xwidth, ywidth]  
            or, if no roi is specified:  
            opens a cv2 window which allows a roi selection
        """
        if self.video_loaded == False:
            print("no video loaded, can't select a ROI")
            return False
        
        if roi is None:
            sel_roi = helpfunctions.sel_roi(self.videometa["prev800px"]) # select roi in 800 px preview img
            roi = [round(coord/self.videometa["prev_scale"]) for coord in sel_roi] # rescale to coord in orig inputdata
            self.analysis_meta["roi"] = roi
            print("selected roi:", roi)
        
        elif isinstance(roi, list):
            self.analysis_meta["roi"] = roi
            print("manually setting roi to", roi)
            # use these coordinates as roi
        
        self._calc_scalingfactor()

    def reset_roi(self):
        """ set roi back to whole frame 
        """
        
        if self.video_loaded == False:
            print("no video loaded, can't reset ROI")
            return False
        self.analysis_meta["roi"] = [0,0,self.videometa['frameWidth'],self.videometa['frameHeight']]
        self._calc_scalingfactor()
        
if __name__ == "__main__":
    OHW = OHW()