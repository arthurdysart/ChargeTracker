# -*- coding: utf-8 -*-
"""
Created on Sat Sep 29 23:32:35 2018

@author: arthur
"""


## IMPORTED MODULES
import os
import os.path as pth
import pickle as pk
import scipy.interpolate as sp
import sys


# FUNCTION DEFINITIONS
def stdin(sys_argv):
    """
    Sets relative paths for serialized electrochemistry models.
    """
    try:
        file_path = str(sys_argv[1]).strip()
    except:
        raise ValueError("Cannot interpret parameter. Check terminal input.")
    return file_path

def serialize_import(file_path):
    """
    Serializes splines as PICKLE file and exports to "models" directory.
    """
    try:
        absolute_path = pth.join(os.getcwd(), pth.normpath(file_path))
        with open(absolute_path, "rb") as pickled_models:
            models = pk.load(pickled_models)
    except:
        raise OSError("Export to directory \"models\" failed.")
    return models


## MAIN MODULE
if __name__ == "__main__":
    file_path = stdin(sys.argv)
    model_charge, model_discharge = serialize_import(file_path)
    print("{}\n{}\n".format(model_charge, model_discharge))
    print("{}\n{}\n".format(type(model_charge), type(model_discharge)))
    print("{}\n{}\n".format(model_charge(0.463), model_discharge(0.121)))


# END OF FILE