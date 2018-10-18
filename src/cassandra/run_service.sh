#!/bin/bash
#
# From the Cassandra master node, initiate the Cassandra service and reset keyspace/tables.
#
# Example:
# bash ~/$CHARGE_TRACKER_HOME/src/cassandra/run_service.sh

CHARGE_TRACKER_HOME=~/charge_tracker
CASSANDRA_HOME=/usr/local/cassandra

# Copies Cassandra settings file
NEW_SETTINGS=$CHARGE_TRACKER_HOME/util/settings/cassandra/cassandra.yaml
OLD_SETTINGS=$CASSANDRA_HOME/conf/cassandra.yaml
sudo cp $NEW_SETTINGS $OLD_SETTINGS

# Starts Cassandra service
sudo cassandra &

# Creates Cassandra keyspace and table
python ~/$CHARGE_TRACKER_HOME/src/cassandra/keyspace_table_reset.py "charge_capacity" "discharge_capacity" "charge_energy" "discharge_energy"