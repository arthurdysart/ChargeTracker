#!/bin/bash
#
# Executes Spark streaming script with required dependencies.
#
# Template:
# bash submit.sh <hostname> <spark-source-script>
# Example:
# bash submit.sh ip-XX-X-X-XX "../../src/spark/cycle_step_analysis.py"

# Initializes hostname and Spark streaming script paths from standard input
HOST_NAME=$1
SPARK_SOURCE=$2
PACKAGES=org.apache.spark:spark-sql-kafka-0-10_2.11:2.3.1,org.apache.spark:spark-streaming-kafka-0-8_2.11:2.0.0,com.databricks:spark-csv_2.11:1.5.0
SPARK_HOME=/usr/local/spark/bin

$SPARK_HOME/spark-submit --master spark://$HOST_NAME:7077 --packages $PACKAGES $SPARK_SOURCE