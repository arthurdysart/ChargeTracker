# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Creates simulated battery cycling data.

Template:
python battery_simulator.py <id> <cycles> <current> <low_voltage_limit> <high_voltage_limit> <models_relative_path>

Example:
python battery_simulator.py 1 10 10000 2.0 4.5 "..\models_generator\models\models_charge_discharge.pk"
"""

## MODULE IMPORTS
from itertools import chain as itl

import datetime as dt
import numpy.random as nprnd
import os.path as pth
import pickle as pk
import sys

## FUNCTION DEFINITIONS

def stdin(sys_argv):
    """
    Imports simulation & Kafka parameters, then assigns battery parameters.
    """
    # Imports terminal input for simulation & Kafka settings
    p = {}
    try:
        p["id"] = int(sys_argv[1])
        p["cycles"] = abs(int(sys_argv[2]))
        p["current"] = abs(float(sys_argv[3]))
        p["v_min"] = float(sys_argv[4])
        p["v_range"] = float(sys_argv[5]) - p["v_min"]
        p["initial_time"] = dt.datetime.now()
    except:
        raise ValueError("Cannot interpret parameters. Check terminal input.")       
    # Imports models from serialized models file
    try:
        models_path = pth.normpath(sys_argv[6])
        with open(models_path, "rb") as pickled_models:
            p["models"] = pk.load(pickled_models)
    except:
        raise OSError("Cannot import models. Check path for models file.")

    # Generates cathode and initial capacity randomly
    p["cathode"] = nprnd.choice(["A", "B", "C", "D",])
    p["capacity"] = nprnd.choice(range(2000, 10001))
    return p

def create_entry(time_stamp, n, step, voltage, p):
    """
    Creates string with format for data entry.
    Schema: <id>, <cathode>, <date_time>, <cycle>, <step>, <voltage>, <current>\n
    """
    date = time_stamp.strftime("%Y-%m-%d %H:%M:%S")
    schema = (str(p["id"]), p["cathode"], date, str(n), step, str(voltage), str(p["current"]),)
    return ", ".join(schema) + "\n"

def generate_step_data(n, step, p):
    """
    For specified cycle & step, generates all line entries.
    """
    # Determines if echem model is for charge or discharge step
    if step is "C":
        model = p["models"][0]
    else:
        model = p["models"][1]

    # If not first charge cycle, Reduces maximum capacity by 96 - 100 %
    if (n, step) != (1, "C"):
        p["capacity"] *= nprnd.choice(range(96, 100)) / 100.0

    # Initializes max time and initial time parameters
    max_step_time = abs(dt.timedelta(seconds=(p["capacity"] * 3600 / p["current"])))
    elasped_time = dt.timedelta(seconds=0)
    # Iterates to publish data entries while elasped time below max time
    while elasped_time < max_step_time:
        delta_time = elasped_time / max_step_time
        voltage = model(delta_time) * p["v_range"] + p["v_min"]
        time_stamp = p["initial_time"] + elasped_time
        yield create_entry(time_stamp, n, step, voltage, p)
        elasped_time += dt.timedelta(seconds=1)
    p["initial_time"] += elasped_time
    return None

def generate_cycle_data(n, p):
    """
    Produces line entries for both "C" and "D" steps for given cycle.
    """
    charge_data = list(generate_step_data(n, "C", p))
    print("Completed cycle {} C.".format(n))
    discharge_data = list(generate_step_data(n, "D", p))
    print("Completed cycle {} D.".format(n))
    return charge_data + discharge_data

def export_data(cycle_data):
    """
    Writes data to export file.
    """
    with open("test_output.txt", "w") as file:
        for line in cycle_data:
            file.write(line)
    return None

## MAIN MODULE
if __name__ == "__main__":

    # Sets simulation parameters for battery simulation
    nprnd.seed(int(sys.argv[1]) * 100 + 20180910)
    p = stdin(sys.argv)

    # Generates data for each battery cycle
    cycle_data = [generate_cycle_data(n, p) for n in range(p["cycles"])]

    # Exports data as text file
    export_data(itl.from_iterable(cycle_data))


# END OF FILE