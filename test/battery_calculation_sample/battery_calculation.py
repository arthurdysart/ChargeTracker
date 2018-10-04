# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Calculates capacity, energy, and power values for sample battery data.

Existing sample data "battery_stdout.txt" generated from Kafka connect using the following command: python battery.py 1 10 1200 2.0 4.5

Template:
python battery_calculation.py <path-to-source> <path-to-output>

Example:
python battery_calculation.py ".\battery_stdout.txt" ".\battery_stdout_analyzed.txt"
"""


## IMPORTED LIBRARIES
import sys
import pandas as pd


## FUNCTION DEFINITIONS
def stdin(sys_argv):
    """
    Imports data from specified file path.
    """
    # Imports parameter values from standard input
    file_path = sys_argv[1]
    path_export = sys_argv[2]
    
    # Imports text file from specified path
    df_input = pd.read_csv(file_path, header=None, sep=", ", engine="python")
    df_input.columns = ["id",
                        "cathode",
                        "cycle",
                        "step",
                        "datetime",
                        "voltage",
                        "current",
                        "prev_voltage",
                        "step_time",]
    # Maps all dataframe values to type float where applicable
    df_input.apply(pd.to_numeric, errors="ignore")
    return df_input, path_export

def calculate_echem(df_input):
    """
    Separates input to calculate instantaneous capacity, energy, and power. 
    """
    # Sets constants for mapping calculations
    DELTA_TIME = 1.0
    CAPACITY_CONVERSION = 3.6E6
    ENERGY_CONVERSION = 3.6E6
    POWER_CONVERSION = 1.0E3

    # Calculates instantaneous capacity as product of current and delta time
    df_capacity = df_input[["id", "cathode", "cycle", "step"]].copy()
    df_capacity["capacity"] = df_input.current * DELTA_TIME \
        / CAPACITY_CONVERSION

    # Calculates instantaneous energy using trapezoid rule
    df_energy = df_input[["id", "cathode", "cycle", "step"]].copy()
    df_energy["energy"] = (df_input.voltage + df_input.prev_voltage) \
        * df_input.current * DELTA_TIME / (2 * ENERGY_CONVERSION)

    # Calculates instantaneous power as product of voltage and current
    df_power = df_input[["id", "cathode", "cycle", "step"]].copy()
    df_power["power"] = (df_input.voltage * df_input.current) \
        / POWER_CONVERSION

    return df_capacity, df_energy, df_power

def group_sum(df_target):
    """
    Calculates sum of target dataframe.
    """
    keys = ["id", "cathode", "cycle", "step"]
    return df_target.groupby(keys).sum()

def group_mean(df_target):
    """
    Calculates mean (average) of target dataframe.
    """
    keys = ["id", "cathode", "cycle", "step"]
    return df_target.groupby(keys).mean()


## MAIN MODULE
if __name__ == "__main__":
    # Imports data as Pandas DataFrame
    df_input, path_export = stdin(sys.argv)

    # Calculates capacity (Amp-hour), energy (Watt-hours), and power (Watts)
    df_capacity, df_energy, df_power = calculate_echem(df_input)

    # Aggregates instantaneous capacity and power by summation
    df_capacity, df_energy = [group_sum(df) for df in (df_capacity, df_energy)]

    # Aggregates instantaneous power by mean
    df_power = group_mean(df_power)

    # Joins capacity, energy, and power into single dataframe
    df_export = df_capacity.join(df_energy).join(df_power)

    # Exports final dataframe to CSV file
    df_export.to_csv(path_export)


## END OF FILE