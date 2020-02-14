# -*- coding: utf-8 -*-

from matplotlib import pyplot as plt
from matplotlib import gridspec
import numpy as np
import pathlib
import moviepy.editor as mpy
from moviepy.video.io.bindings import mplfig_to_npimage
from copy import deepcopy

from libraries import helpfunctions, Filters


def plot_Kinetics(timeindex, motion, plotoptions, hipeaks, lopeaks, motiondescription = "motion", file_name=None):
    """
        plots graph for beating kinetics "EKG"
    """
    print(plotoptions)
    plotoptions_default = {"tmax":None, "vmin":None, "vmax":None, "mark_peaks":False} # default plot parameters, changed if dict is available, implement better checking in future...
    if plotoptions is None:
        plotoptions = plotoptions_default
    else:
        updated_options = deepcopy(plotoptions_default)
        updated_options.update(plotoptions)
        plotoptions = updated_options

    fig_kinetics, ax_kinetics = plt.subplots(1,1,figsize=(11,7))
    ax_kinetics.plot(timeindex, motion, '-', linewidth = 2) #self.fig_kinetics

    tmax = plotoptions["tmax"] if plotoptions["tmax"] != None else timeindex[-1]
    tmin = plotoptions["tmin"] if plotoptions["tmin"] != None else 0
    ax_kinetics.set_xlim(left = tmin, right = tmax)
        
    if plotoptions["vmax"] != None:
        ax_kinetics.set_ylim(top = plotoptions["vmax"])
    if plotoptions["vmin"] != None:
        ax_kinetics.set_ylim(bottom = plotoptions["vmin"])
    
    #self.ax.set_title('Beating kinetics', fontsize = 26)
    ax_kinetics.set_xlabel('t [s]', fontsize = 22)
    ax_kinetics.set_ylabel(motiondescription, fontsize = 22)
    ax_kinetics.tick_params(labelsize = 20)
    
    for side in ['top','right','bottom','left']:
        ax_kinetics.spines[side].set_linewidth(2)              
    
    if plotoptions["mark_peaks"] == True:
        # plot peaks, low peaks are marked as triangles , high peaks are marked as circles         
        ax_kinetics.plot(timeindex[hipeaks], motion[hipeaks], marker='o', ls="", ms=5, color='r')
        ax_kinetics.plot(timeindex[lopeaks], motion[lopeaks], marker='^', ls="", ms=5, color='r')         
    
    if file_name != None:
        fig_kinetics.savefig(str(file_name), dpi = 300, bbox_inches = 'tight') #, bbox_inches = 'tight', pad_inches = 0.4)

def plot_TimeAveragedMotions(ohw_dataset, file_ext='.png'):
    avg_absMotion = ohw_dataset.avg_absMotion
    avg_MotionX, avg_MotionY = ohw_dataset.avg_MotionX, ohw_dataset.avg_MotionY
    max_avgMotion = ohw_dataset.max_avgMotion
    savefolder = ohw_dataset.analysis_meta["results_folder"]
    
    cmap_all = "jet"    #"inferno"
    
    ###### abs-motion
    fig_avgAmp, ax_avg_Amp = plt.subplots(1,1, figsize = (16,12))
    imshow_Amp_avg = ax_avg_Amp.imshow(avg_absMotion, 
        vmin = 0, vmax = max_avgMotion, cmap=cmap_all, interpolation="bilinear")
    cbar = fig_avgAmp.colorbar(imshow_Amp_avg)
    cbar.ax.tick_params(labelsize=16)     

    for l in cbar.ax.yaxis.get_ticklabels():
        l.set_weight("bold")    
      
    ax_avg_Amp.set_title('Average Motion [µm/s]', fontsize = 16, fontweight = 'bold')
    ax_avg_Amp.axis('off')

    outputpath = str(savefolder / ('TimeAveraged_totalMotion' + file_ext))
    fig_avgAmp.savefig(outputpath, dpi = 100, bbox_inches = 'tight', pad_inches = 0.4)

    ##### x-motion
    fig_avgMotionX, ax_avgMotionX = plt.subplots(1,1, figsize = (16,12))
    imshow_Amp_avg = ax_avgMotionX.imshow(avg_MotionX, 
        vmin = 0, vmax = max_avgMotion, cmap=cmap_all, interpolation="bilinear")
    cbar = fig_avgMotionX.colorbar(imshow_Amp_avg)
    cbar.ax.tick_params(labelsize=16)     

    for l in cbar.ax.yaxis.get_ticklabels():
        l.set_weight("bold")    
      
    ax_avgMotionX.set_title('Average x-Motion [µm/s]', fontsize = 16, fontweight = 'bold')
    ax_avgMotionX.axis('off')

    outputpath = str(savefolder / ('TimeAveraged_xMotion' + file_ext))
    fig_avgMotionX.savefig(outputpath, dpi = 100, bbox_inches = 'tight', pad_inches = 0.4)
    
    
    ##### y-motion
    fig_avgMotionY, ax_avgMotionY = plt.subplots(1,1, figsize = (16,12))
    imshow_Amp_avg = ax_avgMotionY.imshow(avg_MotionY, 
        vmin = 0, vmax = max_avgMotion, cmap=cmap_all, interpolation="bilinear")
    cbar = fig_avgMotionY.colorbar(imshow_Amp_avg)
    cbar.ax.tick_params(labelsize=16)     

    for l in cbar.ax.yaxis.get_ticklabels():
        l.set_weight("bold")    
      
    ax_avgMotionY.set_title('Average y-Motion [µm/s]', fontsize = 16, fontweight = 'bold')
    ax_avgMotionY.axis('off')

    outputpath = str(savefolder / ('TimeAveraged_yMotion' + file_ext))
    fig_avgMotionY.savefig(outputpath, dpi = 100, bbox_inches = 'tight', pad_inches = 0.4)
    
def save_heatmap(ohw_dataset, savepath, singleframe = False, *args, **kwargs):
    """
        saves either the selected frame (singleframe = framenumber) or the whole heatmap video (=False)
    """
    absMotions = ohw_dataset.absMotions
    
    savefig_heatmaps, saveax_heatmaps = plt.subplots(1,1)
    savefig_heatmaps.set_size_inches(16,12) 
    saveax_heatmaps.axis('off')
    
    scale_max = helpfunctions.get_scale_maxMotion2(absMotions)
    imshow_heatmaps = saveax_heatmaps.imshow(absMotions[0], vmin = 0, vmax = scale_max, cmap = "jet", interpolation="bilinear")#  cmap="inferno"
    
    cbar_heatmaps = savefig_heatmaps.colorbar(imshow_heatmaps)
    cbar_heatmaps.ax.tick_params(labelsize=20)
    for l in cbar_heatmaps.ax.yaxis.get_ticklabels():
        l.set_weight("bold")
    saveax_heatmaps.set_title('Motion [µm/s]', fontsize = 16, fontweight = 'bold')
    
    '''
    if keyword == None:
        path_heatmaps = self.analysis_meta["results_folder"]/ "heatmap_results"
    elif keyword == 'batch':
        path_heatmaps = subfolder / "heatmap_results"
    '''
    savepath.mkdir(parents = True, exist_ok = True) #create folder for results if it doesn't exist
    
    if singleframe != False:
    # save only specified frame
        imshow_heatmaps.set_data(absMotions[singleframe])
        
        heatmap_filename = str(savepath / ('heatmap_frame' + str(singleframe) + '.png'))
        savefig_heatmaps.savefig(heatmap_filename, bbox_inches = "tight", pad_inches = 0)
    
    else:
    # save video
        fps = ohw_dataset.videometa["fps"]
        
        def make_frame_mpl(t):

            frame = int(round(t*fps))
            imshow_heatmaps.set_data(absMotions[frame])

            return mplfig_to_npimage(savefig_heatmaps) # RGB image of the figure
        
        heatmap_filename = str(savepath / 'heatmapvideo.mp4')
        duration = 1/fps * (absMotions.shape[0] - 1)
        animation = mpy.VideoClip(make_frame_mpl, duration=duration)
        # animation.resize((1500,800))
        animation.write_videofile(heatmap_filename, fps=fps)

def save_quiver(ohw_dataset, savepath, singleframe = False, skipquivers = 1, t_cut = 0, *args, **kwargs):
    """
        saves either the selected frame (singleframe = framenumber) or the whole heatmap video (= False)
        # adjust density of arrows by skipquivers
        # todo: add option to clip arrows
        # todo: maybe move to helpfunctions?
    """
    
    absMotions, unitMVs = ohw_dataset.absMotions, ohw_dataset.unitMVs   
    timeindex = ohw_dataset.timeindex
    analysisImageStack = ohw_dataset.analysisImageStack
    mean_absMotions = ohw_dataset.mean_absMotions
    videometa = ohw_dataset.videometa

    scale_max = helpfunctions.get_scale_maxMotion2(absMotions)   
    MV_zerofiltered = Filters.zeromotion_to_nan(unitMVs, copy=True)
    MV_cutoff = Filters.cutoffMVs(MV_zerofiltered, max_length = scale_max, copy=True)
    # is done twice here... just refer to QuiverMotionX from ohw?
    
    MotionX = MV_cutoff[:,0,:,:]
    MotionY = MV_cutoff[:,1,:,:]

    blockwidth = ohw_dataset.analysis_meta["MV_parameters"]["blockwidth"]
    MotionCoordinatesX, MotionCoordinatesY = np.meshgrid(
            np.arange(blockwidth/2, analysisImageStack.shape[2], blockwidth), 
            np.arange(blockwidth/2, analysisImageStack.shape[1], blockwidth))        
       
    #prepare figure
    fig_quivers, ax_quivers = plt.subplots(1,1, figsize=(14,10), dpi = 150)
    ax_quivers.axis('off')   
    
    qslice=(slice(None,None,skipquivers),slice(None,None,skipquivers))
    distance_between_arrows = blockwidth * skipquivers
    arrowscale = 1 / (distance_between_arrows / scale_max)

    imshow_quivers = ax_quivers.imshow(
            analysisImageStack[0], vmin = videometa["Blackval"], vmax = videometa["Whiteval"], cmap = "gray")

    # adjust desired quiver plotstyles here!
    quiver_quivers = ax_quivers.quiver(
            MotionCoordinatesX[qslice], MotionCoordinatesY[qslice], MotionX[0][qslice], MotionY[0][qslice], 
            pivot='mid', color='r', units ="xy", scale_units = "xy", angles = "xy", scale = arrowscale,  
            width = 4, headwidth = 3, headlength = 5, headaxislength = 5, minshaft =1.5) #width = 4, headwidth = 2, headlength = 3

    #ax_quivers.set_title('Motion [µm/s]', fontsize = 16, fontweight = 'bold')

    savepath.mkdir(parents = True, exist_ok = True) #create folder for results
    
    if singleframe != False:
        # save only specified frame

        imshow_quivers.set_data(analysisImageStack[singleframe])
        quiver_quivers.set_UVC(MotionX[singleframe][qslice], MotionY[singleframe][qslice])
        
        quivers_filename = str(savepath / ('quiver_frame' + str(singleframe) + '.png'))
        fig_quivers.savefig(quivers_filename, bbox_inches ="tight", pad_inches = 0, dpi = 200)
    
    else: 
    # save video
        def make_frame_mpl(t):

            frame = int(round(t*videometa["fps"]))
            imshow_quivers.set_data(analysisImageStack[frame])
            quiver_quivers.set_UVC(MotionX[frame][qslice], MotionY[frame][qslice])
            
            return mplfig_to_npimage(fig_quivers) # RGB image of the figure
        
        quivers_filename = str(savepath / 'quivervideo.mp4')
        duration = 1/videometa["fps"] * (MotionX.shape[0] - 1)
        animation = mpy.VideoClip(make_frame_mpl, duration=duration)
        
        #cut clip if desired by user
        #animation_to_save = self.cut_clip(clip_full=animation, t_cut=t_cut)
        #animation_to_save.write_videofile(quivers_filename, fps=self.videometa["fps"])
        animation.write_videofile(quivers_filename, fps=videometa["fps"])
        
def save_quiver3(ohw_dataset, savepath, singleframe = False, skipquivers = 1, t_cut = 0, *args, **kwargs):
    """
        saves a video with the normal beating, beating + quivers and velocity trace
        or a single frame with the same three views
    """
    
    absMotions, unitMVs = ohw_dataset.absMotions, ohw_dataset.unitMVs   
    timeindex = ohw_dataset.timeindex
    analysisImageStack = ohw_dataset.analysisImageStack
    mean_absMotions = ohw_dataset.mean_absMotions
    videometa = ohw_dataset.videometa
    
    scale_max = helpfunctions.get_scale_maxMotion2(absMotions)   
    MV_zerofiltered = Filters.zeromotion_to_nan(unitMVs, copy=True)
    MV_cutoff = Filters.cutoffMVs(MV_zerofiltered, max_length = scale_max, copy=True)
    
    MotionX = MV_cutoff[:,0,:,:]
    MotionY = MV_cutoff[:,1,:,:]

    blockwidth = ohw_dataset.analysis_meta["MV_parameters"]["blockwidth"]
    MotionCoordinatesX, MotionCoordinatesY = np.meshgrid(
            np.arange(blockwidth/2, analysisImageStack.shape[2], blockwidth), 
            np.arange(blockwidth/2, analysisImageStack.shape[1], blockwidth))        
       
    #prepare figure
    outputfigure = plt.figure(figsize=(14,10), dpi = 150)#figsize=(6.5,12)

    gs = gridspec.GridSpec(3,2, figure=outputfigure)
    gs.tight_layout(outputfigure)
    
    saveax_video = outputfigure.add_subplot(gs[0:2, 0])
    saveax_video.axis('off')        
    
    saveax_quivers = outputfigure.add_subplot(gs[0:2, 1])
    saveax_quivers.axis('off')

    saveax_trace = outputfigure.add_subplot(gs[2,:])
    saveax_trace.plot(timeindex, mean_absMotions, '-', linewidth = 2)
    
    saveax_trace.set_xlim(left = 0, right = timeindex[-1])
    saveax_trace.set_ylim(bottom = 0)
    saveax_trace.set_xlabel('t [s]', fontsize = 22)
    saveax_trace.set_ylabel(u'$\mathrm{\overline {v}}$ [\xb5m/s]', fontsize = 22)
    saveax_trace.tick_params(labelsize = 20)

    for side in ['top','right','bottom','left']:
        saveax_trace.spines[side].set_linewidth(2) 
    
    marker, = saveax_trace.plot(timeindex[0],mean_absMotions[0],'ro')

    ###### prepare video axis
    imshow_video = saveax_video.imshow(
            analysisImageStack[0], vmin = videometa["Blackval"], vmax = videometa["Whiteval"], cmap = "gray")
    
    qslice=(slice(None,None,skipquivers),slice(None,None,skipquivers))
    distance_between_arrows = blockwidth * skipquivers
    arrowscale = 1 / (distance_between_arrows / scale_max)
           
    imshow_quivers = saveax_quivers.imshow(analysisImageStack[0], vmin = videometa["Blackval"], vmax = videometa["Whiteval"], cmap = "gray")
    # adjust desired quiver plotstyles here!
    quiver_quivers = saveax_quivers.quiver(
            MotionCoordinatesX[qslice], MotionCoordinatesY[qslice], MotionX[0][qslice], MotionY[0][qslice], 
            pivot='mid', color='r', units ="xy", scale_units = "xy", angles = "xy", scale = arrowscale,  
            width = 4, headwidth = 3, headlength = 5, headaxislength = 5, minshaft =1.5) #width = 4, headwidth = 2, headlength = 3
            
    #saveax_quivers.set_title('Motion [µm/s]', fontsize = 16, fontweight = 'bold')

    savepath.mkdir(parents = True, exist_ok = True) #create folder for results

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

    # save only specified frame       
    #if not isinstance(singleframe, bool):
    if singleframe != False:
        print("export single frame")
        imshow_quivers.set_data(analysisImageStack[singleframe])
        imshow_video.set_data(analysisImageStack[singleframe])
        quiver_quivers.set_UVC(MotionX[singleframe][qslice], MotionY[singleframe][qslice])
        
        marker.remove()
        marker, = saveax_trace.plot(timeindex[singleframe],mean_absMotions[singleframe],'ro')
        marker.set_clip_on(False)
            
        outputfigure.savefig(str(savepath / ('quiver3_frame' + str(singleframe) + '.png')), bbox_inches = "tight")
              
    else:
        # save video
        def make_frame_mpl(t):
            #calculate the current frame number:
            frame = int(round(t*videometa["fps"]))
            
            imshow_quivers.set_data(analysisImageStack[frame])
            imshow_video.set_data(analysisImageStack[frame])
            
            quiver_quivers.set_UVC(MotionX[frame][qslice], MotionY[frame][qslice])

            #marker.remove() # does not work, only if used as global variable...
            saveax_trace.lines[1].remove()
            marker, = saveax_trace.plot(timeindex[frame],mean_absMotions[frame],'ro')
            marker.set_clip_on(False)
            
            return mplfig_to_npimage(outputfigure)[bbox_bounds_px[1]:bbox_bounds_px[3],bbox_bounds_px[0]:bbox_bounds_px[2]] # RGB image of the figure  #150:1450,100:1950
            
            # slicing here really hacky! find better solution!
            # find equivalent to bbox_inches='tight' in savefig
            # mplfig_to_npimage just uses barer canvas.tostring_rgb()
            # -> check how bbox_inches works under the hood
            # -> in print_figure:
            # if bbox_inches:
            # call adjust_bbox to save only the given area
        
        quivers_filename = str(savepath / 'quivervideo3.mp4')
        duration = 1/videometa["fps"] * (MotionX.shape[0] - 1)
        animation = mpy.VideoClip(make_frame_mpl, duration=duration)
        
        animation.write_videofile(quivers_filename, fps=videometa["fps"])
        #cut clip if desired by user in future
        #animation_to_save = cut_clip(clip_full=animation, t_cut=t_cut)