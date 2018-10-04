# -*- coding: utf-8 -*-
"""
Created on Mon Oct  1 11:41:14 2018

@author: arthur
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
    # Transforms parsed entries into key-value pair
    # SCHEMA: (<battery id: str>, <cathode: str>, <cycle: int>, <step: str>) : (<date-time: str>, <voltage: float>, <current: float>, <prev_voltage: float>, <step_time: float>)
    # HOW TO IDENTIFY AS PAIR RDD?
    paired_rdd = parsed_rdd.map(lambda x: ((int(x[0]), str(x[1]), int(x[2]), str(x[3]),), (str(x[4]), float(x[5]), float(x[6]), float(x[7]), float(x[8]),)))
    paired_rdd.pprint(5)

    # Aggregates voltages prior to calculation of energy and power
    # SCHEMA: (key) : (<date-time:str>, <voltage sum: float>, <current: float>, <step_time: float>, <delta_time: float>)
    preeval_rdd = paired_rdd.map(lambda x: (x[0], (x[1][0], x[1][1] + x[1][3], x[1][2], x[1][4], 1.0,)))
    preeval_rdd.pprint(5)

    # Calculates incremental energy and weighted power for each data entry
    # SCHEMA: (key) : (<incremental energy: float>, <weighted power: float>)
    calc_rdd = preeval_rdd.map(lambda x: (x[0], (x[1][1] * x[1][2] * x[1][4], x[1][1] * x[1][2] * x[1][4] / x[1][3],)))
    calc_rdd.pprint(5)

    # For each key, sums incremental energy and weighted power for each data entry
    # SCHEMA: (key) : (<total energy: float>, <average power: float>)
    summed_rdd = calc_rdd.reduceByKey(lambda i, j: (i[0] + j[0], i[1] + j[1]))
    summed_rdd.pprint(5)

    return summed_rdd

def save_to_database(input_rdd, table_name):
    """
    For each micro-RDD, sends partition to target database.
    Requires "send_partition" function.
    """
    # ConnectionPool is a static, lazily initialized pool of connections
    #connection = ConnectionPool.getConnection()
    #for record in input_rdd:
    #    connection.send(record)
    # return to the pool for future reuse
    #ConnectionPool.returnConnection(connection)

    input_rdd.foreachRDD(lambda rdd: rdd.foreachPartition(send_partition))
    #input_rdd.foreachRDD(lambda entries: send_partition(entries, table_name))

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
                cmd_batch = cassq.BatchStatement(consistency_level=cass.ConsistencyLevel.QUORUM)
    
        # Executes final set of batches and closes Cassandra session
        db_cass.execute(cmd_batch)
        db_cass.shutdown()
    
        return None

    return None


## MAIN MODULE
if __name__ == "__main__":
    # Sets Kafka and Cassandra parameters
    p = stdin(sys.argv)
    # Initializes spark context SC and streaming context SCC
    sc = SparkContext(appName=p["spark_name"])
    sc.setLogLevel("WARN")
    ssc = StreamingContext(sc, 30)
    kafka_stream = kfk.createDirectStream(ssc, p["kafka_topic"], {"bootstrap.servers": p["kafka_broker"]})

    # For each micro-RDD, strips whitespace and split by comma
    parsed_rdd = kafka_stream.map(lambda ln: (x.strip() for x in ln[1].strip().split(",")))

    # For each micro-RDD, transforms instantaneous measurements to overall values in RDD
    summed_rdd = summarize_step_data(parsed_rdd)
    #summed_rdd.persist()

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
