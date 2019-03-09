# -*- coding: utf-8 -*-

from matplotlib import pyplot as plt
import numpy as np
import pathlib

def plot_Kinetics(timeindex, mean_absMotions, Peaks, mark_peaks, file_name):
    """
        plots graph for beating kinetics "EKG"
    """
    fig_kinetics, ax_kinetics = plt.subplots(1,1)
    fig_kinetics.set_size_inches(11, 7) #16,12  
    
    ax_kinetics.plot(timeindex, mean_absMotions, '-', linewidth = 2) #self.fig_kinetics
    ax_kinetics.set_xlim(left = 0, right = timeindex[-1])
    ax_kinetics.set_ylim(bottom = 0)
    #fig_kinetics.subplots_adjust(bottom = 0.2)
    
    #self.ax.set_title('Beating kinetics', fontsize = 26)
    ax_kinetics.set_xlabel('t [s]', fontsize = 22)
    ax_kinetics.set_ylabel(u'Mean Absolute Motion [\xb5m/s]', fontsize = 22)
    ax_kinetics.tick_params(labelsize = 20)
    
    for side in ['top','right','bottom','left']:
        ax_kinetics.spines[side].set_linewidth(2)              
    
    if (mark_peaks == True): #Peaks["t_peaks_low_sorted"] != None
        # plot peaks, low peaks are marked as triangles , high peaks are marked as circles         
        ax_kinetics.plot(Peaks["t_peaks_low_sorted"], Peaks["peaks_low_sorted"], marker='o', ls="", ms=5, color='r' )
        ax_kinetics.plot(Peaks["t_peaks_high_sorted"], Peaks["peaks_high_sorted"], marker='^', ls="", ms=5, color='r' )  #easier plotting without for loop          
    
    fig_kinetics.savefig(file_name, dpi = 300, bbox_inches = 'tight') #, bbox_inches = 'tight', pad_inches = 0.4)
    

def plot_TimeAveragedMotions(avg_absMotion, avg_MotionX, avg_MotionY, max_avgMotion, savefolder, file_ext):
    colormap_for_all = "jet"    #"inferno"
    
    ###### abs-motion
    fig_avgAmp, ax_avg_Amp = plt.subplots(1,1)
    fig_avgAmp.set_size_inches(16, 12)
    imshow_Amp_avg = ax_avg_Amp.imshow(avg_absMotion, vmin = 0, vmax = max_avgMotion, cmap=colormap_for_all, interpolation="bilinear")
    cbar = fig_avgAmp.colorbar(imshow_Amp_avg)
    cbar.ax.tick_params(labelsize=16)     

    for l in cbar.ax.yaxis.get_ticklabels():
        l.set_weight("bold")    
      
    ax_avg_Amp.set_title('Average Motion [µm/s]', fontsize = 16, fontweight = 'bold')
    ax_avg_Amp.axis('off')

    outputpath = str(savefolder / ('TimeAveraged_totalMotion' + file_ext))
    fig_avgAmp.savefig(outputpath, dpi = 100, bbox_inches = 'tight', pad_inches = 0.4)

    ##### x-motion
    fig_avgMotionX, ax_avgMotionX = plt.subplots(1,1)
    fig_avgMotionX.set_size_inches(16, 12)
    imshow_Amp_avg = ax_avgMotionX.imshow(avg_MotionX, vmin = 0, vmax = max_avgMotion, cmap=colormap_for_all, interpolation="bilinear")
    cbar = fig_avgMotionX.colorbar(imshow_Amp_avg)
    cbar.ax.tick_params(labelsize=16)     

    for l in cbar.ax.yaxis.get_ticklabels():
        l.set_weight("bold")    
      
    ax_avgMotionX.set_title('Average x-Motion [µm/s]', fontsize = 16, fontweight = 'bold')
    ax_avgMotionX.axis('off')

    outputpath = str(savefolder / ('TimeAveraged_xMotion' + file_ext))
    fig_avgMotionX.savefig(outputpath, dpi = 100, bbox_inches = 'tight', pad_inches = 0.4)
    
    
    ##### y-motion
    fig_avgMotionY, ax_avgMotionY = plt.subplots(1,1)
    fig_avgMotionY.set_size_inches(16, 12)
    imshow_Amp_avg = ax_avgMotionY.imshow(avg_MotionY, vmin = 0, vmax = max_avgMotion, cmap=colormap_for_all, interpolation="bilinear")
    cbar = fig_avgMotionY.colorbar(imshow_Amp_avg)
    cbar.ax.tick_params(labelsize=16)     

    for l in cbar.ax.yaxis.get_ticklabels():
        l.set_weight("bold")    
      
    ax_avgMotionY.set_title('Average y-Motion [µm/s]', fontsize = 16, fontweight = 'bold')
    ax_avgMotionY.axis('off')

    outputpath = str(savefolder / ('TimeAveraged_yMotion' + file_ext))
    fig_avgMotionY.savefig(outputpath, dpi = 100, bbox_inches = 'tight', pad_inches = 0.4)