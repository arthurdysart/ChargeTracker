# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Calculates capacity, energy, and power values for sample battery data.

Existing sample data "battery_stdout.txt" generated from Kafka connect using the following command: python battery.py 1 10 1200 2.0 4.5

Template:
python table_reset.py <table-name-1> <table-name-2> ... <table-name-N>

Example:
python table_reset.py "energy" "power"
"""


## MODULE IMPORTS
import cassandra as cass
import cassandra.cluster as cassc
import cassandra.query as cassq
import decouple as dc
import os
import sys


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

    # Imports Cassandra settings
    try:
        p = {}
        p["cassandra"] = settings.get("CASSANDRA_MASTER", cast=dc.Csv())
        p["cassandra_key"] = settings.get("CASSANDRA_KEYSPACE")
        table_names = [name for name in sys_argv[1:]]
    except:
        raise ValueError("Cannot interpret parameters. Check terminal input.")

    return table_names, p

def setup_connection(p):
    """
    Initializes Cassandra CQL session and batch CQL statement executor.
    """
    db_cass = cassc.Cluster(p["cassandra"]).connect(p["cassandra_key"])
    cmd_batch = cassq.BatchStatement(consistency_level=cass.ConsistencyLevel.QUORUM)
    return db_cass, cmd_batch

def reset_table(table_name, db_cass, cql_batch):
    """
    Creates and executes CQL commands to drop and re-create Cassandra tables.
    """
    print("Respawning table {} ...".format(table_name))

    # Creates CQL command for dropping existing table
    cql_drop = """ DROP TABLE IF EXISTS {}; """.format(table_name)
    db_cass.execute(cql_drop)

    # Creates CQL command for creating table
    cql_create = """ CREATE TABLE IF NOT EXISTS {}(id int, cathode text,
    cycle int, step text, {} float, PRIMARY KEY(id, cathode, cycle, step))
    WITH CLUSTERING ORDER BY (cathode DESC, cycle DESC); """ \
    .format(table_name, table_name)
    db_cass.execute(cql_create)

    return 1


## MAIN MODULE
if __name__ == "__main__":
    # Imports standard input
    table_names, p = stdin(sys.argv)

    # Setup Cassandra cluster connection
    db_cass, cql_batch = setup_connection(p)

    # Creates all CQL commands for table reset
    count = sum(reset_table(name, db_cass, cql_batch) for name in table_names)
    db_cass.shutdown()

    print("Reset {} tables: {}".format(count, ", ".join(table_names)))


## END OF FILE