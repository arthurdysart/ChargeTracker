#!/bin/bash
#
# Produces multiple battery data generators using TMUX.
#
# Template:
# bash reset_topic.sh <KAFKA_TOPIC> <PARTITIONS> <REPLICATION>
# Example:
# bash reset_topic.sh battery_data 1 3

# Sets Kafka parameters from standard input
KAFKA_TOPIC=$1
PARTITIONS=$2
REPLICATION=$3
KAFKA_HOME=/usr/local/kafka/bin

# Deletes existing Kafka topic
$KAFKA_HOME/kafka-topics.sh --zookeeper localhost:2181 --delete --topic '"$KAFKA_TOPIC"'
echo "Wait 20 minutes for deletion..."
sleep 20m

# Re-creates Kafka topic
$KAFKA_HOME/kafka-topics.sh --zookeeper localhost:2181 --create --topic '"$KAFKA_TOPIC"' --partitions '"$PARTITION"' --replication-factor '"$REPLICATION"'
echo "Created topic: $KAFKA_TOPIC"