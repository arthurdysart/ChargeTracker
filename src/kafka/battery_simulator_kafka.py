# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Publishes simulated battery cycling data to created kafka producer.

Template:
python battery_simulator_kafka.py <id> <cycles> <current> <low_voltage_limit> <high_voltage_limit>

Example:
python battery_simulator_kafka.py 1 1000 200 2.0 4.5
"""

## MODULE IMPORTS
import datetime as dt
import decouple as dc
import kafka.producer as kk
import numpy.random as nprnd
import os.path as pth
import pickle as pk
import sys


## FUNCTION DEFINITIONS

def stdin(sys_argv):
    """
    Imports simulation & Kafka parameters, then assigns battery parameters.
    """
    # Sets sensitive variables from ENV file
    path_settings = pth.normpath(r"..\..\util\project_settings\.env")
    settings = dc.Config(dc.RepositoryEnv(path_settings))
    # Imports terminal input for simulation & Kafka settings
    try:
        p = {}
        p["id"] = int(sys_argv[1])
        p["cycles"] = range(abs(int(sys_argv[2])))
        p["current"] = abs(float(sys_argv[3]))
        p["v_min"] = float(sys_argv[4])
        p["v_range"] = float(sys_argv[5]) - p["v_min"]
        p["kafka_broker"] = settings.get("KAFKA_BROKER")
        p["kafka_topic"] = settings.get("KAFKA_TOPIC")
        p["initial_time"] = dt.datetime.now()
    except:
        raise ValueError("Cannot interpret parameters. Check terminal input.")

    # Imports models from serialized models file
    try:
        models_path = pth.normpath(settings.get("PATH_MODELS"))
        with open(models_path, "rb") as pickled_models:
            p["models"] = pk.load(pickled_models)
    except:
        raise OSError("Cannot import models. Check path for models file.")

    # Generates cathode and initial capacity randomly
    p["cathode"] = nprnd.choice(["A", "B", "C", "D",])
    p["capacity"] = nprnd.choice(range(2000, 10001))
    return p

def create_entry(date_time, n, step, voltage, p):
    """
    Creates string with format for data entry.
    Schema: <id>, <cathode>, <dt>, <cycle>, <step>, <voltage>, <current>\n
    """
    date_time = date_time.strftime("%Y-%m-%d %H:%M:%S:%f")
    schema = (str(p["id"]),
              p["cathode"],
              date_time,
              str(n),
              step,
              str(voltage),
              str(p["current"]),)
    return ", ".join(schema) + "\n"

def generate_step_data(n, step, p, kafka_prod):
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

    # Initializes time parameters
    max_time = abs(dt.timedelta(seconds=(p["capacity"] * 3600 / p["current"])))
    elasped_time = dt.timedelta(seconds=0)

    # Generates and publishes data entries while elasped time below max time
    while elasped_time <= max_time:
        delta_time = elasped_time / max_time
        voltage = model(delta_time) * p["v_range"] + p["v_min"]
        date_time = p["initial_time"] + elasped_time
        entry = create_entry(date_time, n, step, voltage, p)
        kafka_prod.send(p["kafka_topic"], entry)
        elasped_time += dt.timedelta(seconds=1)
    p["initial_time"] += elasped_time

    return None

def generate_cycle_data(n, p, kafka_prod):
    """
    Produces line entries for both "C" and "D" steps for given cycle.
    """
    generate_step_data(n, "C", p, kafka_prod)
    generate_step_data(n, "D", p, kafka_prod)
    return 2

## MAIN MODULE
if __name__ == "__main__":
    # Sets simulation parameters for battery simulation
    nprnd.seed(int(sys.argv[1]) * 100 + 20180910)
    p = stdin(sys.argv)

    # Creates Kafka producer
    kafka_prod = kk.KafkaProducer(bootstrap_servers=p["kafka_broker"])

    # Generates data for each battery cycle, and publishes to Kafka broker
    count = sum(generate_cycle_data(n, p, kafka_prod) for n in p["cycles"])
    print("Finished processing {} steps.".format(count))


# END OF FILE