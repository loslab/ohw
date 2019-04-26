# -*- coding: utf-8 -*-

from matplotlib import pyplot as plt
import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
from PIL import ImageDraw, ImageFont, Image

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
    
def msgbox(self, message):
    """
        display message in QMessageBox
    """
    msg_text = message
    msg_title = 'Successful'
    msg = QMessageBox.information(self, msg_title, msg_text, QMessageBox.Ok)
    if msg == QMessageBox.Ok:
        pass  
        
def scale_ImageStack(imageStack, px_longest = 1024):
    """
        rescales imageStack such that longest side equals px_longest
    """
    w, h = imageStack.shape[1], imageStack.shape[2]
    longest_side = max(w,h)
    scalingfactor = px_longest/longest_side
    
    
    scaledImages = []
    for image in imageStack:
        scaledImages.append(cv2.resize(image, None, fx = scalingfactor, fy = scalingfactor))

    scaledImageStack = np.array(scaledImages)
    print("shape of scaled down image stack: ", scaledImageStack.shape)
    print("scalingfactor: ", scalingfactor)
    
    return scaledImageStack, scalingfactor