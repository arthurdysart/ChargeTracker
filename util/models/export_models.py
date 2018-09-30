# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Fits imported echem data to SCIPY spline objects, then exports to PICKLE file.

Template:
python export_models.py <model_charge_relative_path> <model_discharge_relative_path>

Example:
python export_models.py "cobalt-oxide_charge.csv" "cobalt-oxide_discharge.csv"
"""


## IMPORTED MODULES
import numpy as np
import os
import os.path as pth
import pickle as pk
import scipy.interpolate as sp
import sys


## FUNCTION DEFINITIONS
def stdin(sys_argv):
    """
    Sets relative paths for electrochemistry models to import.
    """
    try:
        model_charge_path = str(sys_argv[1]).strip()
        model_discharge_path = str(sys_argv[2]).strip()
    except:
        raise ValueError("Cannot interpret parameters. Check terminal input.")
    return model_charge_path, model_discharge_path

def read_csv(file_path):
    """
    Reads and saves input data as numpy array.
    """
    try:
        absolute_path = pth.join(os.getcwd(), pth.normpath(file_path))
        with open(absolute_path, "r") as file:
            imported_csv = [list(map(float, line.split(","))) for line in file]
    except:
        raise OSError("Cannot find file: {}".format(absolute_path))
    return np.array(imported_csv)

def normalize(series):
    """
    Normalizes data series according to maximum value.
    """
    # Adjusts series to minimum value of zero
    series = series - min(series)
    # Scales series to maximum value of one
    new_series = series / max(series)
    return new_series

def create_spline(dataset):
    """
    Fits dataset to spline object.
    """
    abcissa = normalize(dataset[:,0])
    ordinate = normalize(dataset[:,1])
    # Fits input data to spline function
    spline = sp.interp1d(abcissa, ordinate)
    return spline

def serialize_export(splines):
    """
    Serializes splines as PICKLE file and exports to "models" directory.
    """
    try:
        dir_home = os.getcwd()
        os.chdir("models")
        with open("models_charge_discharge.pk", "wb") as pickled_models:
            pk.dump(tuple(splines), pickled_models)
        dir_export = os.getcwd()
        os.chdir(dir_home)
    except:
        raise OSError("Export to directory \"models\" failed.")
    return dir_export


## MAIN MODULE
if __name__ == "__main__":
    model_paths = stdin(sys.argv)
    data = [read_csv(path) for path in model_paths]
    splines = [create_spline(dataset) for dataset in data]
    print("{}\n{}\n".format(splines[0](0.463), splines[1](0.121)))
    dir_export = serialize_export(splines)
    print("Saved models to directory:\n{}\n".format(dir_export))


## END OF MODULE