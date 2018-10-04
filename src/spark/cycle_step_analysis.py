# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Transforms RDDs from Kafka direct stream (DStream) into capacity, energy, and
power values for given CQL command batch size. Data is reduced by aggregate or
primary key: <(0) battery-id, (1) cathode, (2) cycle, (3) step>.

Existing sample data "battery_stdout.txt" generated from Kafka connect using the following command: python battery.py 1 10 1200 2.0 4.5

Template:
python cassandra_reset.py <table-name-1> <table-name-2> ... <table-name-N>

Example:
python cassandra_reset.py "energy" "power"
"""

## REQUIRED MODULES
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils as kfk

import cassandra as cass
import cassandra.cluster as cassc
import cassandra.query as cassq
import decouple as dc
import os
import sys


## FUNCTION DEFINITIONS
def stdin(sys_argv):
    """
    Imports Kafka & Cassandra parameters.
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
        p["spark_name"]= settings.get("SPARK_NAME")
        p["cassandra"] = settings.get("CASSANDRA_MASTER", cast=dc.Csv())
        p["cassandra_key"] = settings.get("CASSANDRA_KEYSPACE")
        p["kafka_broker"] = settings.get("KAFKA_BROKER")
        p["kafka_topic"] = settings.get("KAFKA_TOPIC", cast=dc.Csv())
    except:
        raise ValueError("Cannot interpret external settings. Check ENV file.")

    return p

def summarize_step_data_old(parsed_rdd):
    """
    For each battery, cycle, and step (KEYS), calculates total energy and average power.
    """
    # Transforms parsed entries into key-value pair
    # SCHEMA: (<battery id: str>, <cathode: str>, <cycle: int>, <step: str>) : (<date-time: str>, <voltage: float>, <current: float>, <prev_voltage: float>, <step_time: float>)
    # HOW TO IDENTIFY AS PAIR RDD?
    paired_rdd = parsed_rdd.map(lambda x: ((int(x[0]), str(x[1]), int(x[2]), str(x[3]),), (str(x[4]), float(x[5]), float(x[6]), float(x[7]), float(x[8]),)))

    # Aggregates voltages prior to calculation of energy and power
    # SCHEMA: (key) : (<date-time:str>, <voltage sum: float>, <current: float>, <step_time: float>, <delta_time: float>)
    preeval_rdd = paired_rdd.map(lambda x: (x[0], (x[1][0], x[1][1] + x[1][3], x[1][2], x[1][4], 1.0,)))

    # Calculates incremental energy and weighted power for each data entry
    # SCHEMA: (key) : (<incremental energy: float>, <weighted power: float>)
    calc_rdd = preeval_rdd.map(lambda x: (x[0], (x[1][1] * x[1][2] * x[1][4], x[1][1] * x[1][2] * x[1][4] / x[1][3],)))

    # For each key, sums incremental energy and weighted power for each data entry
    # SCHEMA: (key) : (<total energy: float>, <average power: float>)
    summed_rdd = calc_rdd.reduceByKey(lambda i, j: (i[0] + j[0], i[1] + j[1]))

    return summed_rdd

def summarize_step_data(parsed_rdd):
    """
    For each battery, cycle, and step (KEYS), calculates total energy and average power.
    """
    # Sets constants for mapping calculations
    DELTA_TIME = 1.0
    CAPACITY_CONVERSION = 3.6E6
    ENERGY_CONVERSION = 3.6E6
    POWER_CONVERSION = 1.0E3
    
    # Transforms parsed entries into key-value pair
    # SCHEMA: (<battery id: str>, <cathode: str>, <cycle: int>, <step: str>) : (<date-time: str>, <voltage: float>, <current: float>, <prev_voltage: float>, <step_time: float>)
    # HOW TO IDENTIFY AS PAIR RDD?
    paired_rdd = parsed_rdd.map(lambda x: ((int(x[0]), str(x[1]), int(x[2]), str(x[3]),), (str(x[4]), float(x[5]), float(x[6]), float(x[7]), float(x[8]),)))

    # Calculates instantaneous capacity, energy, and power for each entry
    # SCHEMA: (key) : (<capacity: float>, <energy: float>, <power: float>, <counts: int>)
    inst_rdd = paired_rdd.map(lambda x: (x[0],
                                         x[1][2] * DELTA_TIME / CAPACITY_CONVERSION,
                                         x[1][2] * (x[1][1] + x[1][3]) * DELTA_TIME / (2 * ENERGY_CONVERSION),
                                         x[1][2] * x[1][1] / POWER_CONVERSION,
                                         1))

    # Calculates total capacity and energy, and power sum for each key
    # SCHEMA: (key) : (<total capacity: float>, <total energy: float>, <power sum: float>, <count sum: float>)
    total_rdd = inst_rdd.reduceByKey(lambda i, j: (i[0] + j[0],
                                                   i[1] + j[1],
                                                   i[2] + j[2],
                                                   i[3] + j[3]))

    # Calculates total capacity and energy, and power sum for each key
    # SCHEMA: (key) : (<total energy: float>, <average power: float>)
    final_rdd = total_rdd.map(lambda x: (x[0],
                                         x[1][0],
                                         x[1][1],
                                         x[1][2] / x[1][3]))

    return final_rdd

def send_partition(entries, table_name):
    """
    Collects rdd entries and sends as batch of CQL commands.
    Required by "save_to_database" function.
    """

    # Initializes keyspace and CQL batch executor in Cassandra database
    db_cass = cassc.Cluster(p["cassandra"]).connect(p["cassandra_key"])
    cmd_batch = cassq.BatchStatement(consistency_level=cass.ConsistencyLevel.QUORUM)
    cmd_size = 0

    # Prepares CQL statement with appropriate values
    if "energy" in table_name.lower():
        cql_schema = "INSERT INTO energy (id, cathode, cycle, step, energy) VALUES (?, ?, ?, ?, ?)"
    elif "power" in table_name.lower():
        cql_schema = "INSERT INTO power (id, cathode, cycle, step, power) VALUES (?, ?, ?, ?, ?)"
    elif "capacity" in table_name.lower():
        cql_schema = "INSERT INTO capacity (id, cathode, cycle, step, capacity) VALUES (?, ?, ?, ?, ?)"
    else:
        raise SyntaxError("Cannot find specified table. Check name and run again.")
    cql_statement = db_cass.prepare(cql_schema)

    # Iterates over all entries in rdd partition
    for entry in entries:
        cmd_batch.add(cql_statement, entry)
        cmd_size += 1
        # Executes collected CQL commands on Cassandra keyspace, and re-initializes collection
        if cmd_size % 500 == 0:
            db_cass.execute(cmd_batch)
            cmd_batch = cassq.BatchStatement(consistency_level= \
                                             cass.ConsistencyLevel.QUORUM)

    # Executes final set of batches and closes Cassandra session
    db_cass.execute(cmd_batch)
    db_cass.shutdown()

    return None

def save_to_database(input_rdd, table_name):
    """
    For each micro-RDD, sends partition to target database.
    Requires "send_partition" function.
    """
    input_rdd.foreachRDD(lambda rdd: \
        rdd.foreachPartition(lambda entries: \
            send_partition(entries, table_name)))
    return None


## MAIN MODULE
if __name__ == "__main__":
    # Sets Kafka and Cassandra parameters
    p = stdin(sys.argv)
    # Initializes spark context SC and streaming context SCC
    sc = SparkContext(appName=p["spark_name"])
    sc.setLogLevel("WARN")
    ssc = StreamingContext(sc, 30)
    kafka_stream = kfk.createDirectStream(ssc, \
                                          p["kafka_topic"], \
                                          {"bootstrap.servers": \
                                              p["kafka_broker"]})

    # For each micro-RDD, strips whitespace and split by comma
    parsed_rdd = kafka_stream.map(lambda ln: tuple(x.strip() for x in ln[1].strip().split(",")))

    # For each micro-RDD, transforms instantaneous measurements to overall values in RDD
    summed_rdd = summarize_step_data(parsed_rdd)

    # Transforms overall values to CQL format for storage in Cassandra database
    # SCHEMA: (<battery id: str>, <cathode: str>, <cycle: int>, <step: str>, <total energy>)
    energy_rdd = summed_rdd.map(lambda x: (x[0][0], x[0][1], x[0][2], x[0][3], x[1][0]))
    save_to_database(energy_rdd, "energy")

    # Transforms overall values to CQL format for storage in Cassandra database
    # SCHEMA: (<battery id: str>, <cathode: str>, <cycle: int>, <step: str>, <average power>)
    power_rdd = summed_rdd.map(lambda x: (x[0][0], x[0][1], x[0][2], x[0][3], x[1][1]))
    save_to_database(power_rdd, "power")

    # Unpersists overall values RDD
    #summed_rdd.unpersist()

    # Starts and stops spark streaming context
    ssc.start()
    ssc.awaitTermination()


## END OF FILE