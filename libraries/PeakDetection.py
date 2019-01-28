# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import numpy as np
import pathlib
from scipy.signal import argrelextrema
from PyQt5.QtWidgets import QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from openpyxl import Workbook
from openpyxl.styles import Font


class PeakDetection():
    def __init__(self):
        self.mean_absMotions = None
        self.timeindex = None
        self.peaktimes_th = None  #times of thresholded peaks
        self.peak_heights_th = None  # peakheights of thresholded peaks
        self.sorted_peaks = None  # list of sorted peaks (high/low) and corresponding times
        self.peakstatistics = None # list of peakstatistics: max_contraction, std, max_relaxation, std
        self.time_intervals = None # list of calculated intervals and std: contraction, relaxation, contr-rel
        self.bpm = None # list of bpm + std
        self.foundPeaks = 0  # number of found peaks
        # having dicts for these variables would be much nicer!
    
    def set_data(self, timeindex, mean_absMotions):
        """
            reads in x,y datapairs (timeindex, mean_absMotions) and resets all output dicts
        """
        self.mean_absMotions = mean_absMotions
        self.timeindex = timeindex
        self.foundPeaks = 0
        
        self.peaktimes_th = None
        self.peak_heights_th = None
        
        self.sorted_peaks = {"t_peaks_low_sorted":None,"peaks_low_sorted":None,"t_peaks_high_sorted":None,"peaks_high_sorted":None}
        self.peakstatistics = {"max_contraction":None, "max_contraction_std": None, "max_relaxation": None, "max_relaxation_std": None}

        self.time_intervals = {"contraction_interval_mean":None, "contraction_interval_std":None, "relaxation_interval_mean":None, "relaxation_interval_std":None, "contr_relax_interval_mean":None, "contr_relax_interval_std":None}
        self.bpm = {"bpm_mean":None, "bpm_std": None}
        
    def detectPeaks(self, ratio, number_of_neighbours):
        
        print("detecting peaks with ratio: ", ratio, " and neighbours: ", number_of_neighbours)
        
        peaks = argrelextrema(self.mean_absMotions, np.greater, order=number_of_neighbours)
        peakpos = np.array(peaks[0])  #location of peaks in inputarray
        
        #remove peaks that are smaller than a certain threshold, e.g. ratio = 1/15
        peak_heights = self.mean_absMotions[peakpos]
        threshold = ratio * np.max(peak_heights)
        peakpos_th = peakpos[peak_heights > threshold]  #th=thresholded?
        
        self.peaktimes_th = self.timeindex[peakpos_th]
        self.peak_heights_th = self.mean_absMotions[peakpos_th]
        
        self.foundPeaks = self.peaktimes_th.shape[0] #set number of found peaks
        
        print(self.foundPeaks, " peaks found")
        
    def analyzePeaks(self): 
        """
            splits peaks into low and high peaks (= relaxation, contraction)
            sets self.sorted_peaks, self.peakstatistics (contraction + relaxation times)
        """
        
        if self.foundPeaks < 2:
            print("only ", self.foundPeaks, " peaks detected, which are not enough for the analysis")
            return
        
        sort_index_height = self.peak_heights_th.argsort()
        
        #peak_heights_sorted = np.sort(self.peak_heights_th)
        peak_heights_sorted = self.peak_heights_th[sort_index_height]
        peaktimes_sorted = self.peaktimes_th[sort_index_height]
        peak_differences = np.diff(peak_heights_sorted)
        
        max_difference_index = np.argmax(peak_differences)+1
        peaks_low = peak_heights_sorted[0:max_difference_index]
        peaks_high = peak_heights_sorted[max_difference_index:]
        
        t_peaks_low = peaktimes_sorted[0:max_difference_index]
        t_peaks_high = peaktimes_sorted[max_difference_index:]
        print(t_peaks_low, peaks_low)
        print(t_peaks_high, peaks_high)
        
        #sort the high and low peaks along the time axis
        sort_index_t_high = np.argsort(t_peaks_high)
        sort_index_t_low = np.argsort(t_peaks_low)
        
        t_peaks_high_sorted = t_peaks_high[sort_index_t_high]
        t_peaks_low_sorted = t_peaks_low[sort_index_t_low]
        peaks_high_sorted = peaks_high[sort_index_t_high]
        peaks_low_sorted = peaks_low[sort_index_t_low]
        
        decimals = 4
        max_contraction     = np.round(np.mean(peaks_high), decimals)
        max_contraction_std = np.round(np.std(peaks_high),  decimals)
        max_relaxation      = np.round(np.mean(peaks_low),  decimals)
        max_relaxation_std  = np.round(np.std(peaks_low),   decimals)
        
        #self.sorted_peaks = [t_peaks_low_sorted, peaks_low_sorted, t_peaks_high_sorted, peaks_high_sorted]
        self.sorted_peaks = {"t_peaks_low_sorted":t_peaks_low_sorted,"peaks_low_sorted":peaks_low_sorted,"t_peaks_high_sorted":t_peaks_high_sorted,"peaks_high_sorted":peaks_high_sorted}
        #self.peakstatistics = [max_contraction, max_contraction_std, max_relaxation, max_relaxation_std]
        self.peakstatistics = {"max_contraction":max_contraction, "max_contraction_std": max_contraction_std, "max_relaxation": max_relaxation, "max_relaxation_std": max_relaxation_std}
        
    def calculateTimeIntervals(self):
        """
            calculates contraction and relaxation intervals
            sets self.time_intervals, self.bpm
        """
        
        if self.foundPeaks < 2:
            return       
        
        t_peaks_low = self.sorted_peaks["t_peaks_low_sorted"]  #, peaks_low, t_peaks_high, peaks_high = self.sorted_peaks
        t_peaks_high = self.sorted_peaks["t_peaks_high_sorted"]
        
        contraction_intervals = np.diff(np.sort(t_peaks_high))
        relaxation_intervals = np.diff(np.sort(t_peaks_low))
        
        #print(contraction_intervals, relaxation_intervals)
        #calculate interval from contraction to next relaxation
        contr_relax_intervals = []
        for low_peak, high_peak in zip(t_peaks_low, t_peaks_high):
            # depending on which peak is first the true interval might be from the next peak on....
            time_difference = low_peak - high_peak           
            contr_relax_intervals.append(np.abs(time_difference))
            """
            # not clear what happens here?
            #TO DO: ADJUST -0.6!!
            if (time_difference < 0) & (time_difference > -0.6):
                time_difference = -time_difference
                
            if time_difference > 0:
                contr_relax_intervals.append(time_difference)
            """
            
        #statistics on time intervals
        decimals = 4    
        contraction_interval_mean = np.round(np.mean(contraction_intervals), decimals)
        contraction_interval_std = np.round(np.std(contraction_intervals), decimals)
        relaxation_interval_mean = np.round(np.mean(relaxation_intervals), decimals)
        relaxation_interval_std = np.round(np.std(relaxation_intervals), decimals)
        contr_relax_interval_mean = np.round(np.mean(np.asarray(contr_relax_intervals)), decimals)
        contr_relax_interval_std = np.round(np.std(np.asarray(contr_relax_intervals)), decimals)
        
        #convert to beats per minute
        bpm_mean = np.round(np.mean(60/contraction_intervals), decimals)
        bpm_std = np.round(np.std(60/contraction_intervals), decimals)
        
        #calculate time intervals and heart rate (bpm)        
        #self.time_intervals = [contraction_interval_mean, contraction_interval_std, relaxation_interval_mean, relaxation_interval_std, contr_relax_interval_mean, contr_relax_interval_std]
        self.time_intervals = {"contraction_interval_mean":contraction_interval_mean, "contraction_interval_std":contraction_interval_std, "relaxation_interval_mean":relaxation_interval_mean, "relaxation_interval_std":relaxation_interval_std, "contr_relax_interval_mean":contr_relax_interval_mean, "contr_relax_interval_std":contr_relax_interval_std}
        self.bpm = {"bpm_mean":bpm_mean, "bpm_std": bpm_std}
        #self.bpm = [bpm_mean, bpm_std]

    def export_peaks(self, results_folder):
        #save peaks to an excel file:
        
        workbook_peaks = Workbook()
        sheet = workbook_peaks.active
        sheet.Name = 'Peaks_raw'
        sheet.append(['time','mean absolute motion'])
        
        for time, peak in zip(self.peaktimes_th, self.peak_heights_th):
            sheet.append([time, peak])
        
        #save analyzed peaks to an excel file:
        workbook_analyzed_peaks = Workbook()
        sheet_analyzed = workbook_analyzed_peaks.active
        sheet_analyzed.Name = 'Peaks_analyzed'
        sheet_analyzed.append(['time', 'mean absolute motion', 'high/low'])        

        for time, peak in zip(self.sorted_peaks["t_peaks_low_sorted"], self.sorted_peaks["peaks_low_sorted"]):
            sheet_analyzed.append([time, peak, "low"])       

        for time, peak in zip(self.sorted_peaks["t_peaks_high_sorted"], self.sorted_peaks["peaks_high_sorted"]):
            sheet_analyzed.append([time, peak, "high"])                

        #define the saving location:
        save_file = str(results_folder / 'Peaks_raw.xlsx')
        save_file_analyzed = str(results_folder / 'Peaks_analyzed.xlsx')
        
        #save the peaks
        workbook_peaks.save(save_file)
        workbook_analyzed_peaks.save(save_file_analyzed)
    
    def exportEKG_CSV(self, results_folder):
        font_bold = Font(bold=True) 
        
        workbook_ekg = Workbook()
        sheet_ekg = workbook_ekg.active
        sheet_ekg.Name = 'EKG values'
        sheet_ekg.append(['Values of the EKG:'])
        sheet_ekg.append(['time (sec)', 'mean absolute motion'])

        for time, peak in zip(self.timeindex, self.mean_absMotions):
            sheet_ekg.append([time, peak])        
        
        #turn some cells'style to bold
        bold_cells = ['A1', 'B1', 'C1', 'A2', 'B2', 'C2']

        for cell in bold_cells:
            sheet_ekg[cell].font = font_bold
        
        #save peaks
        save_file = str(results_folder / 'EKG.xlsx')
        workbook_ekg.save(save_file)
    
    def exportStatistics(self, results_folder, inputpath, blockwidth, delay, fps, maxShift, scalingfactor):
        font_bold = Font(bold=True)                     
        workbook_statistics = Workbook()
        
        sheet = workbook_statistics.active
        sheet.Name = 'Statistics'
        
        #add the used parameters
        sheet.append(['Evaluated file/ folder: ', str(inputpath)])
        sheet.append(['Used parameters:', '', 'unit'])
        sheet.append(['scaling factor for calculation: ', scalingfactor, 'rel. to input'])
        sheet.append(['width of macroblocks ', blockwidth, 'pixels'])
        sheet.append(['delay between images', delay, 'frames'])
        sheet.append(['framerate', fps, 'frames/sec'])
        sheet.append(['maximum allowed movement ', maxShift, 'pixels'])
        
        #add the statistical results         
        sheet.append([''])
        sheet.append(['Results of statistical analysis:'])
        sheet.append(['result', 'mean', 'standard deviation', 'unit'])
        sheet.append(['maximum contraction', self.peakstatistics["max_contraction"], self.peakstatistics["max_contraction_std"], u'\xb5m/sec'])
        sheet.append(['maximum relaxation', self.peakstatistics["max_relaxation"], self.peakstatistics["max_relaxation_std"], u'\xb5m/sec'])
        sheet.append(['mean contraction interval', self.time_intervals["contraction_interval_mean"], self.time_intervals["contraction_interval_std"], 'sec'])
        sheet.append(['mean relaxation interval', self.time_intervals["relaxation_interval_mean"], self.time_intervals["relaxation_interval_std"], 'sec'])
        sheet.append(['mean interval between contraction and relaxation', self.time_intervals["contr_relax_interval_mean"], self.time_intervals["contr_relax_interval_std"], 'sec'])
        sheet.append(['heart rate', self.bpm["bpm_mean"], self.bpm["bpm_std"], 'beats/min'])
             
        #turn some cells'style to bold
        bold_cells = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12', 'A13', 'A14', 'A15', 'A16', 'B10', 'C2','C10', 'D10']

        for cell in bold_cells:
            sheet[cell].font = font_bold
            
        #save the file 
        save_file = str(results_folder / 'Statistics.xlsx')
        workbook_statistics.save(save_file)