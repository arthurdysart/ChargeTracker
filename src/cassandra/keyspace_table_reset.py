# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Refreshes keyspace "battery_metrics" and charge/discharge capacity/energy tables.

Template:
python keyspace_table_reset.py <table-name-1> <table-name-2> ... <table-name-N>

Example:
python keyspace_table_reset.py "charge_capacity" "discharge_capacity" "charge_energy" "discharge_energy"
"""


## MODULE IMPORTS
import cassandra.cluster as cassc
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
        table_names = [name for name in sys_argv[1:]]
    except:
        raise ValueError("Cannot interpret parameters. Check input.")
    return table_names, p

def setup_connection(p):
    """
    Initializes Cassandra CQL session and batch CQL statement executor.
    """
    db_cass = cassc.Cluster(p["cassandra"])
    return db_cass

def reset_keyspace(keyspace_name, db_cass):
    """
    Creates and executes CQL commands for Cassandra keyspace and UDFs.
    """
    # Initialzes keyspace
    db_cass.execute("""
                    DROP KEYSPACE IF EXISTS {};
                    """.format(keyspace_name))

    db_cass.execute("""
                    CREATE KEYSPACE IF NOT EXISTS {}
                    WITH replication =
                    {'class': 'SimpleStrategy',
                    'replication_factor' : 3};
                    """.format(keyspace_name))

    # Creates CQL command for double and integer summation
    db_cass.execute("""
                    CREATE OR REPLACE FUNCTION
                    double_sum (collection list<double>)
                    CALLED ON NULL INPUT RETURNS double
                    LANGUAGE java AS
                    'double sum = 0;
                    for (double i: collection)
                    { sum += i; }
                    return sum;';
                    """)

    db_cass.execute("""
                    CREATE OR REPLACE FUNCTION
                    int_sum (collection list<int>)
                    CALLED ON NULL INPUT RETURNS int
                    LANGUAGE java AS
                    'int sum = 0;
                    for (int i: collection)
                    { sum += i; }
                    return sum;';
                    """)
    return None

def reset_table(table_name, db_cass):
    """
    Creates and executes CQL commands to drop and re-create Cassandra tables.
    """
    print("Respawning table {} ...".format(table_name))

    db_cass.execute("""
                    DROP TABLE IF EXISTS {};
                    """.format(table_name))

    db_cass.execute("""
                    CREATE TABLE IF NOT EXISTS {} (
                    cathode text,
                    cycle int,
                    id int,
                    value list<double>,
                    PRIMARY KEY((cathode, cycle)));
                    """.format(table_name))
    return 1


## MAIN MODULE
if __name__ == "__main__":
    # Imports standard input and sets Cassandra connection
    table_names, p = stdin(sys.argv)
    db_cass = setup_connection(p)

    # Creates and executes all CQL commands for keyspace reset
    reset_keyspace("battery_metrics", db_cass)

    # Creates and executes all CQL commands for table reset
    count = sum(reset_table(name, db_cass) for name in table_names)

    # Ends CQL session and displays completion statement to standard output
    db_cass.shutdown()
    print("Reset {} tables: {}".format(count, ", ".join(table_names)))


## END OF FILE