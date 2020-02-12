# -*- coding: utf-8 -*-

from matplotlib import pyplot as plt
import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
from PIL import ImageDraw, ImageFont, Image
import requests
import configparser
import math

def get_figure_size(img, initial_val):
    ratio = img.shape[0]/img.shape[1]
    mini = min(img.shape[0], img.shape[1])
    #if dim1 is shorter
    if mini == img.shape[0]:
        width = initial_val*ratio
        height = initial_val
    else:
        width = initial_val
        height = initial_val/ratio

    return width, height

def turn_function_into_thread(inputfunction, emit_progSignal=False, *arg, **kwargs):
    class ThreadedFunction(QThread):
        # create signal if wanted
        if emit_progSignal == True:
            progressSignal = pyqtSignal(float)
        else:
            progressSignal = False
            
        def __init__(self, inputfunction, *arg, **kwargs):
            QThread.__init__(self)
            #self.stop_flag = False

        # run method gets called when we start the thread
        def run(self):
            #print("kwargs:", kwargs)
            inputfunction(progressSignal = self.progressSignal, *arg, **kwargs)
        
        def isAlive(self):
            self.isAlive()
            
        def endThread(self):
            self.terminate()
      
    return ThreadedFunction(inputfunction)

def create_scalebar(dimX_px, microns_per_pixel):
    """
        creates scalebar as np array which then can be transferred to image
        returns uint8 array, min: 0 (black), max: 255 (white)
    """
    
    scale_values = [1,2,5,10,15,20,30,40,50,70,100,150,200,300,400,500,700,1000]
    initial_scale_length = dimX_px * 0.2 * microns_per_pixel
    
    text_height_px = int(round(dimX_px * 0.05))
    drawfont = ImageFont.truetype("arial.ttf", text_height_px)
    
    scale_length_microns = min(scale_values, key=lambda x:abs(x-initial_scale_length))    # pick nearest value
    scale_caption = str(scale_length_microns) + " µm"
    scale_length_px = scale_length_microns / microns_per_pixel
    scale_height_px = dimX_px * 0.01
    
    bg_square_spacer_px = scale_length_px * 0.07
    
    bg_square_length_px = int(round(scale_length_px + 2 * bg_square_spacer_px))
    bg_square_height_px = int(round(text_height_px + scale_height_px + 2 * bg_square_spacer_px))
    
    scalebar = Image.new("L", (bg_square_length_px, bg_square_height_px), "white") #L corresponds to black & white image
    draw = ImageDraw.Draw(scalebar)
    
    w_caption, h_caption = draw.textsize(scale_caption, font = drawfont)        
     
    draw.rectangle(((0, 0), (bg_square_length_px, bg_square_height_px)), fill="black")
    draw.rectangle(((bg_square_spacer_px, bg_square_height_px - bg_square_spacer_px - scale_height_px), (bg_square_length_px - bg_square_spacer_px, bg_square_height_px - bg_square_spacer_px)), fill="white")
    draw.text((bg_square_spacer_px + bg_square_length_px/2 - w_caption/2, bg_square_spacer_px/2), scale_caption, font = drawfont, fill="white") #white = 255
    
    output_scalebar = np.array(scalebar)
    return output_scalebar

def insert_scalebar(imageStack, videometa, analysis_meta):
    '''
        inserts scalebar into imageStack (3D-Array)
        take care: modifies imageStack
    '''
    sizeX = imageStack.shape[1]
    resolution_units = videometa["microns_per_pixel"] / analysis_meta["scalingfactor"]
    scalebar = helpfunctions.create_scalebar(sizeX,resolution_units)*(videometa["Whiteval"]/255)    #/255 works, check again...
    scale_width_px = scalebar.shape[0]
    scale_height_px = scalebar.shape[1]
    imageStack[:,-1-scale_width_px:-1,-1-scale_height_px:-1] = scalebar    
    
def msgbox(self, message, msg_title = 'Successful'):
    """
        display message in QMessageBox
    """
    msg_text = message
    msg = QMessageBox.information(self, msg_title, msg_text, QMessageBox.Ok)
    if msg == QMessageBox.Ok:
        pass  
        
def scale_ImageStack(imageStack, px_longest = 1024):
    """
        rescales imageStack such that longest side equals px_longest
        upscaling of smaller stack is prevented
    """
    w, h = imageStack.shape[1], imageStack.shape[2]
    longest_side = max(w,h)
    scalingfactor = px_longest/longest_side
    
    if scalingfactor >= 1: #prevent upscaling
        return imageStack, 1
    
    scaledImages = []
    for image in imageStack:
        scaledImages.append(cv2.resize(image, None, fx = scalingfactor, fy = scalingfactor))

    scaledImageStack = np.array(scaledImages)
    print("shape of scaled down image stack: ", scaledImageStack.shape)
    print("scalingfactor: ", scalingfactor)
    
    return scaledImageStack, scalingfactor
    
def get_scale_maxMotion(absMotions, mean_absMotions):
    """
        --> deprecated
        returns maximum for scaling of heatmap + arrows in quiver
        selects frame with max motion (= one pixel), picks 95th percentile in this frame as scale max
        ... find better metric
        #max_motion = self.mean_maxMotion
        #scale_max = np.mean(self.OHW.absMotions)    #should be mean of 1d-array of max motions
        #scale_max = np.mean(np.max(self.OHW.absMotions,axis=(1,2)))
    """
    
    max_motion_framenr = np.argmax(mean_absMotions)
    max_motion_frame = absMotions[max_motion_framenr]
    scale_min, scale_maxMotion = np.percentile(max_motion_frame, (0.1, 95))
    return scale_maxMotion

def get_scale_maxMotion2(absMotions):
    """
        returns maximum for scaling of heatmap + arrows in quiver
        input absMotions: 3D ndarray (framenr/Motion(x/y))
        v2: takes all frames into account, select positions where motion > 0, max represents 80th percentile
    """
    
    absMotions_flat = absMotions[absMotions>0].flatten()
    scale_min, scale_maxMotion = np.percentile(absMotions_flat, (0, 80))   
    return scale_maxMotion
    
def check_update(self, curr_version):
    try:
        print('try checking for updates')
        github_config = requests.get('https://raw.github.com/loslab/ohw/master/config.ini').text
        config = configparser.ConfigParser()
        config.read_string(github_config)
        github_version = config['UPDATE']['version']
        github_version = tuple(map(int, (github_version.split("."))))# split version string 1.1.1 into tuple (1,1,1)
        curr_version = tuple(map(int, (curr_version.split("."))))
        if github_version > curr_version:
            message = "A new version is available. Download the newest version from:<br><a href='https://github.com/loslab/ohw'>https://github.com/loslab/ohw</a>"
            msgbox(self, message=message, msg_title = 'Update available')
    except Exception as e:
        print('Could not check for update:', e)

def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config
        
def save_config(config):
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def create_prev(img, height = 800):
    """ creates preview image to be stored in ohw class in 800 px """
    if len(img.shape) == 3: # converts to gray if rgb image
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    (h, w) = img.shape[:2]
    scale = height/h
    width = int(scale*w)
    img_prev = cv2.resize(img, (width, height))
    
    return img_prev

def sel_roi(img):
    """
        allows selection of roi in image
        returns roi xstart, ystart, xwidth, ywidth in px
    """
    # to do: add something to prevent display of crazy aspect ratios
    
    window_height = 800
    
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)      
    hpercent = (window_height / float(img.shape[0]))
    wsize = int(round((float(img.shape[1]) * float(hpercent))))
    hsize = window_height
    image_scaled = cv2.resize(img, (wsize, hsize))    
    
    roi = list(cv2.selectROI('Press Enter to save the currently selected ROI:', image_scaled, fromCenter=False))
    cv2.destroyAllWindows()
    # returns: xstart, ystart, xwidth, ywidth, in display coordinates
    # returns old roi if ESC is pressed
    
    # if selection is drawn outside window: crop
    if (roi[0] + roi[2] > wsize):
        roi[2] = wsize - roi [0]
    if (roi[1] + roi[3] > hsize):
        roi[3] = hsize - roi [1]
    
    # negative start
    if roi[0] < 0:
        roi[2] = roi[2] + roi[0]
        roi[0] = 0
    if roi[1] < 0:
        roi[3] = roi[3] + roi[1]
        roi[1] = 0
    
    roi_px = [int(round(coord/hpercent)) for coord in roi]

    return roi_px
    
def get_slice_from_roi(roi, blockwidth):
    """ input roi: [xs, ys, wx, wy]
        so far: includes only MVs which are completely in roi, calculated motionvector (= whole block) has to be completely in roi
        e.g. bw = 8, roi from 4 - 400 -> start with 2nd MV (index = 1), up to 50th MV: 1:50
        e.g. bw = 8, roi from 1 (=px 2) with width = 15 (= px 16) -> 2nd MV only selected (index = 1): 1:2
        
        todo: double check finally if array dimensions x/y are not somehow flipped!
    """
    
    xs,ys,wx,wy = roi
    
    bw = blockwidth
    
    xs = xs
    ys = ys
    
    xe = xs + wx
    ye = ys + wy
    
    MVxs = math.ceil(xs/bw)
    MVxe = math.floor(xe/bw)
    
    if MVxe < MVxs: # special case if start and end are in same MV, would lead to slice
        MVxe = MVxs
    
    MVys = math.ceil(ys/bw)
    MVye = math.floor(ye/bw)
    
    if MVye < MVys: 
        MVye = MVys
        
    slicex = slice(MVxs, MVxe)
    slicey = slice(MVys, MVye)
    
    return(slicex, slicey)