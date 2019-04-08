# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 15:45:16 2019

@author: sailca
"""

#write config file
import configparser
import pathlib


config = configparser.ConfigParser()

config['DEFAULT VALUES'] = {'blockwidth':   16,
                            'delay':        2,
                            'maxShift':     7,
                            'fps':          17.49105135069209,
                            'px_per_micron':1.5374
                            }
config['DEFAULT QUIVER SETTINGS'] = {'one_view':        'true',
                                     'three_views':     'false',
                                     'show_scalebar':   'true',
                                     'quiver_density':  2,
                                     'video_length':    0.00
                                     }

config['LAST SESSION'] = {'input_folder': str((pathlib.Path(__file__) / ".." / "..").resolve())#,
                         # 'results_folder': str((pathlib.Path(__file__) / ".." / "..").resolve())
                          }

with open('config.ini', 'w') as configfile:
    config.write(configfile)