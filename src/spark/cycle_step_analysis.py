# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Transforms RDDs from Kafka direct stream (DStream) into capacity, energy, and
power values for given CQL command batch size. Data is reduced by aggregate or
primary key: <(0) battery-id, (1) cathode, (2) cycle, (3) step>. Separate
database tables are created for capacity, energy, and power.

To use, call from script "spark_submit.sh".
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


    # ORDER BY DATA?

    # Calculates instantaneous capacity, energy, and power for each entry
    # SCHEMA: (key) : (<capacity: float>, <energy: float>, <power: float>, <counts: int>)
    inst_rdd = paired_rdd.map(lambda x: (x[0],
                                         (x[1][2] * DELTA_TIME / CAPACITY_CONVERSION,
                                         x[1][2] * (x[1][1] + x[1][3]) * DELTA_TIME / (2 * ENERGY_CONVERSION),
                                         x[1][2] * x[1][1] / POWER_CONVERSION,
                                         1)))

    # Calculates total capacity and energy, and power sum for each key
    # SCHEMA: (key) : (<total capacity: float>, <total energy: float>, <power sum: float>, <count sum: float>)
    total_rdd = inst_rdd.reduceByKey(lambda i, j: (i[0] + j[0],
                                                   i[1] + j[1],
                                                   i[2] + j[2],
                                                   i[3] + j[3]))

    # Calculates total capacity and energy, and power sum for each key
    # SCHEMA: (key) : (<total energy: float>, <average power: float>)
    summary_rdd = total_rdd.map(lambda x: (x[0],
                                           x[1][0],
                                           x[1][1],
                                           x[1][2] / x[1][3]))

    return summary_rdd

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

def save_to_file(input_rdd, file_name):
    """
    For each micro-RDD, saves input data to text file.
    """
    input_rdd.foreachRDD(lambda rdd: rdd.saveAsTextFile(file_name)) #open(file_name, "a").write(str(rdd)))
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
    summary_rdd = summarize_step_data(parsed_rdd)
    save_to_file(summary_rdd, r"/home/ubuntu/overview/src/spark/dstream_stdout/summary.txt")
    #summary_rdd.saveAsTextFiles("./dstream_stdout/summary")


    # Transforms overall values to CQL format for storage in Cassandra database
    # SCHEMA: (<battery id: str>, <cathode: str>, <cycle: int>, <step: str>, <total capacity>)
    capacity_rdd = summary_rdd.map(lambda x: (x[0][0], x[0][1], x[0][2], x[0][3], x[1]))
    save_to_database(capacity_rdd, "capacity")
    save_to_file(capacity_rdd, r"/home/ubuntu/overview/src/spark/dstream_stdout/capacity.txt")
    #capacity_rdd.saveAsTextFiles("./dstream_stdout/capacity")

    # Transforms overall values to CQL format for storage in Cassandra database
    # SCHEMA: (<battery id: str>, <cathode: str>, <cycle: int>, <step: str>, <total energy>)
    energy_rdd = summary_rdd.map(lambda x: (x[0][0], x[0][1], x[0][2], x[0][3], x[2]))
    save_to_database(energy_rdd, "energy")
    save_to_file(energy_rdd, r"/home/ubuntu/overview/src/spark/dstream_stdout/energy.txt")
    #energy_rdd.saveAsTextFiles("./dstream_stdout/energy")

    # Transforms overall values to CQL format for storage in Cassandra database
    # SCHEMA: (<battery id: str>, <cathode: str>, <cycle: int>, <step: str>, <average power>)
    power_rdd = summary_rdd.map(lambda x: (x[0][0], x[0][1], x[0][2], x[0][3], x[3]))
    save_to_database(power_rdd, "power")
    save_to_file(power_rdd, r"/home/ubuntu/overview/src/spark/dstream_stdout/power.txt")
    #power_rdd.saveAsTextFiles("./dstream_stdout/power")

    # Starts and stops spark streaming context
    ssc.start()
    ssc.awaitTermination()


## END OF FILE