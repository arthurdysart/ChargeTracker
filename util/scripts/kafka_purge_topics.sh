#!/bin/bash
#
# Deletes all topics from Kafka.
#
# Example:
# bash kafka_purge_topics.sh

# Gets all current topics in Kafka
KAFKA_HOME=/usr/local/kafka/bin
TOPICS=$($KAFKA_HOME/kafka-topics.sh --list --zookeeper localhost:2181)
echo "Found topics: $TOPICS"

# Iterates deletion over all found topics
for TOPIC in $TOPICS;
do
    echo "Deleting topic $TOPIC ..."
    $KAFKA_HOME/kafka-topics.sh --zookeeper localhost:2181 --delete --topic $TOPIC
done

echo "All topics marked for deletion. Check topics in a few minutes to confirm."