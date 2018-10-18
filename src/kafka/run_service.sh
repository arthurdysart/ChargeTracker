#!/bin/bash
#
# From the Kafka master node, initiate the Kafka service and create partitioned Kafka topic.
#
# Example:
# bash ~/$CHARGE_TRACKER_HOME/src/Kafka/run_service.sh

CHARGE_TRACKER_HOME=~/charge_tracker
KAFKA_HOME=/usr/local/kafka

# Copies Kafka settings file
NEW_SETTINGS=$CHARGE_TRACKER_HOME/util/settings/kafka/server.properties
OLD_SETTINGS=$KAFKA_HOME/config/server.properties
sudo cp $NEW_SETTINGS $OLD_SETTINGS

# Starts Kafka service
KAFKA_START=$KAFKA_HOME/bin/kafka-server-start.sh
sudo $KAFKA_START $OLD_SETTINGS &

# Creates Kafka message topic with 3 partitions and 3 replicas
bash topic_reset.sh "battery_data" "3" "3"