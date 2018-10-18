# -*- coding: utf-8 -*-
"""
Publishes simulated battery cycling data to created kafka producer.

Template:
python battery_python-kafka.py <seed> <cycles> <current> <low_voltage_limit> <high_voltage_limit>

Example:
python battery_python-kafka.py 1 1000 200 2.0 4.5
"""

## MODULE IMPORTS
import datetime as dt
import decouple as dc
import kafka.producer as kk
import numpy.random as nprnd
import os
import pickle as pk
import sys
import uuid as uu


## FUNCTION DEFINITIONS

def stdin(sys_argv):
    """
    Imports simulation & Kafka parameters, then assigns battery parameters.
    """
    # Sets sensitive variables from ENV file
    try:
        path_home = os.getcwd()
        os.chdir(r"../../util/settings")
        settings = dc.Config(dc.RepositoryEnv(".env"))
        os.chdir(path_home)
    except:
        raise OSError("Cannot import ENV settings. Check path for ENV.")

    # Imports terminal input for simulation & Kafka settings
    try:
        p = {}
        p["id"] = uu.uuid4()
        p["cycles"] = range(abs(int(sys_argv[2])))
        p["current"] = abs(float(sys_argv[3]))
        p["v_min"] = float(sys_argv[4])
        p["v_range"] = float(sys_argv[5]) - p["v_min"]
        p["kafka_brokers"] = settings.get("KAFKA_BROKERS", cast=dc.Csv())
        p["kafka_topic"] = settings.get("KAFKA_TOPIC")
        p["initial_time"] = dt.datetime.now()
    except:
        raise ValueError("Cannot interpret parameters. Check terminal input.")

    # Imports models from serialized models file
    try:
        os.chdir(r"../../util/models")
        with open("models_charge_discharge.pk", "rb") as pickled_models:
            p["models"] = pk.load(pickled_models)
    except:
        raise OSError("Cannot import models. Check path for models file.")

    # Generates cathode and initial capacity pseudo-randomly
    p["cathode"] = nprnd.choice(["W", "X", "Y", "Z",])

    if p["cathode"] == "W":
        p["capacity"] = nprnd.choice(range(5000, 6001))
    elif p["cathode"] == "X":
        p["capacity"] = nprnd.choice(range(9500, 12001))
    elif p["cathode"] == "Y":
        p["capacity"] = nprnd.choice(range(2000, 8001))
    else:
        p["capacity"] = nprnd.choice(range(4500, 9001))
    return p

def create_entry(date_time, n, step, voltage, voltage_prev, max_time, p):
    """
    Creates string with format for data entry.
    Schema: <id>, <cathode>, <dt>, <cycle>, <step>, <voltage>, <current>\n
    """
    #date_time_0 = p["initial_time"].strftime("%Y-%m-%d %H:%M:%S")
    date_time = date_time.strftime("%Y-%m-%d %H:%M:%S")
    schema = (str(p["id"]),
              p["cathode"],
              str(n),
              step,
              date_time,
              str(voltage),
              str(p["current"]),
              str(voltage_prev),
              str(max_time),)
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

    # If not first charge cycle, Reduces maximum capacity by 99.0 - 99.9 %
    if (n, step) != (1, "C"):
        p["capacity"] *= nprnd.choice(range(9900, 10000)) / 10000.0
        p["voltage_prev"] = -1 * (model(0.0) * p["v_range"] + p["v_min"])

    # Initializes time parameters
    max_time = abs(dt.timedelta(seconds=(p["capacity"] * 3600 / p["current"])))
    elasped_time = dt.timedelta(seconds=0)

    # Generates and publishes data entries while elasped time below max time
    while elasped_time <= max_time:
        delta_time = elasped_time.total_seconds() / max_time.total_seconds()
        voltage = model(delta_time) * p["v_range"] + p["v_min"]
        date_time = p["initial_time"] + elasped_time
        entry = create_entry(date_time, n+1, step, voltage, p["voltage_prev"], max_time.total_seconds(), p)
        kafka_prod.send(p["kafka_topic"], entry)
        p["voltage_prev"] = voltage
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
    nprnd.seed(int(sys.argv[1]) * 400 + 20180910)
    p = stdin(sys.argv)

    # Creates Kafka producer
    kafka_prod = kk.KafkaProducer(bootstrap_servers=p["kafka_brokers"])

    # Generates data for each battery cycle, and publishes to Kafka broker
    count = sum(generate_cycle_data(n, p, kafka_prod) for n in p["cycles"])


# END OF FILE
