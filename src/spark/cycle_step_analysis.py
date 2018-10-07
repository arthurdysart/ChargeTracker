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

def summarize_step_data(kafka_stream):
    """
    For each entry, calculates capacity, energy, power sum, and counts.
    """
    # Sets constants for mapping calculations
    DELTA_TIME = 1.0
    CAP_CONVERSION = 3.6E6
    ENG_CONVERSION = 3.6E6
    PWR_CONVERSION = 1.0E3

    # For each micro-RDD, strips whitespace and split by comma
    parsed_rdd = kafka_stream.map(lambda ln: \
        tuple(x.strip() for x in ln[1].strip().split(",")))
    #parsed_rdd.pprint(3)

    # Transforms parsed entries into key-value pair
    # SCHEMA: (<battery id: str>, <cathode: str>, <cycle: int>, <step: str>) :
    #         (<date-time: str>, <voltage: float>, <current: float>,
    #          <prev_voltage: float>, <step_time: float>)
    paired_rdd = parsed_rdd.map(lambda x: \
        ((int(x[0]), str(x[1]), int(x[2]), str(x[3]),), \
         (str(x[4]), float(x[5]), float(x[6]), float(x[7]), float(x[8]),)))
    #paired_rdd.pprint(3)
    
    # Calculates instantaneous capacity, energy, and power for each entry
    # SCHEMA: (key) :
    #         (<capacity: float>, <energy: float>, <power: float>,
    #          <counts: int>)
    inst_rdd = paired_rdd.map(lambda x: \
        (x[0], \
        (x[1][2] * DELTA_TIME / CAP_CONVERSION, \
         x[1][2] * (x[1][1] + x[1][3]) * DELTA_TIME / (2 * ENG_CONVERSION), \
         x[1][2] * x[1][1] / PWR_CONVERSION, \
         1,)))
    #inst_rdd.pprint(3)

    # Calculates total capacity and energy, and power sum for each key
    # SCHEMA: (key) :
    #         (<total capacity: float>, <total energy: float>,
    #          <power sum: float>, <count sum: float>)
    total_rdd = inst_rdd.reduceByKey(lambda i, j: \
        (i[0] + j[0], \
         i[1] + j[1], \
         i[2] + j[2], \
         i[3] + j[3],))
    #total_rdd.pprint(3)

    # Re-organizes key and value contents for Cassandra CQL interpolation
    # SCHEMA: <cathode: str>, <total capacity: float>, <total energy: float>,
    #         <power sum: float>, <counts: float>, <step: str>, <cycle: int>,
    #         <battery id: str>
    summary_rdd = total_rdd.map(lambda x: \
        (x[0][1], \
         x[1][0], \
         x[1][1], \
         x[1][2], \
         x[1][3], \
         x[0][3], \
         x[0][2], \
         x[0][0],))
    #summary_rdd.pprint(3)

    return summary_rdd

def send_partition(entries, table_name, crit_size=500):
    """
    Collects rdd entries and sends as batch of CQL commands.
    Required by "save_to_database" function.
    """

    # Initializes keyspace and CQL batch executor in Cassandra database
    db_cass = cassc.Cluster(p["cassandra"]).connect(p["cassandra_key"])
    cql_batch = cassq.BatchStatement(consistency_level= \
                                     cass.ConsistencyLevel.QUORUM)
    batch_size = 0

    # Prepares CQL statement, with interpolated table name, and placeholders
    cql_command = db_cass.prepare("""
                                  UPDATE {} SET
                                  capacity =  ? + capacity,
                                  energy = ? + energy,
                                  power = ? + power,
                                  counts = ? + counts
                                  WHERE step = ? AND cycle = ? AND id = ?;
                                  """.format(table_name))

    for e in entries:
        # Interpolates prepared CQL statement with values from entry
        print("*****************************************************")
        print("{}".format(e))
        print("{}".format(type(e)))
        print("*****************************************************")
        cql_batch.add(cql_command, parameters= \
                      [cassq.ValueSequence((e[1],)), \
                       cassq.ValueSequence((e[2],)), \
                       cassq.ValueSequence((e[3],)), \
                       cassq.ValueSequence((e[4],)), \
                       e[5], \
                       e[6], \
                       e[7],])
        batch_size += 1
        # Executes collected CQL commands, then re-initializes collection
        if batch_size == crit_size:
            db_cass.execute(cql_batch)
            cql_batch = cassq.BatchStatement(consistency_level= \
                                             cass.ConsistencyLevel.QUORUM)
            batch_size = 0

    # Executes final set of remaining batches and closes Cassandra session
    db_cass.execute(cql_batch)
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

    EXAMPLE:
    save_to_file(parsed_rdd, "/home/ubuntu/overview/src/spark/dstream_stdout/{}.txt")
    """
    input_rdd.foreachRDD(lambda rdd: open(file_name, "a") \
                         .write(str(rdd.collect()) + "\n"))
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

    # For each micro-RDD, transforms instantaneous measurements to overall values in RDD
    summary_rdd = summarize_step_data(kafka_stream)

    # For each cathode, filters data and sends to Cassandra database
    for cathode in ["W", "X", "Y", "Z"]:
        filtered_rdd = summary_rdd.filter(lambda x: str(x[0]).upper() != cathode)
        filtered_rdd.pprint(10)
        save_to_database(filtered_rdd, "cathode_{}".format(cathode))

    # Starts and stops spark streaming context
    ssc.start()
    ssc.awaitTermination()


## END OF FILE