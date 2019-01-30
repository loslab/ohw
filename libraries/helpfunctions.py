# -*- coding: utf-8 -*-

from matplotlib import pyplot as plt
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from PIL import ImageDraw, ImageFont, Image

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
            inputfunction(progressSignal = self.progressSignal, *arg, **kwargs)
      
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