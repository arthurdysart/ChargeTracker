#!/bin/bash
#
# From the Spark driver node, initiate the Spark Streaming service and run DStream MapReduce tasks.
#
# Example:
# bash ~/$CHARGE_TRACKER_HOME/src/spark/run_service.sh

CHARGE_TRACKER_HOME=~/charge_tracker
SPARK_HOME=/usr/local/spark

# Copies Spark settings and environment files
NEW_SETTINGS=$CHARGE_TRACKER_HOME/util/settings/spark/spark-defaults.conf
OLD_SETTINGS=$SPARK_HOME/conf/spark-defaults.conf
sudo cp $NEW_SETTINGS $OLD_SETTINGS
NEW_ENV=$CHARGE_TRACKER_HOME/util/settings/spark/spark-env.sh
OLD_ENV=$SPARK_HOME/conf/spark-env.sh
sudo cp $NEW_ENV $OLD_ENV

# Starts Spark streaming service
bash $SPARK_HOME/sbin/start-all.sh

# Execute Spark streaming script
SPARK_START=$SPARK_HOME/spark-submit
SPARK_MASTER=spark://localhost:7077
SPARK_PACKAGES=org.apache.spark:spark-sql-kafka-0-10_2.11:2.3.1,org.apache.spark:spark-streaming-kafka-0-8_2.11:2.0.0,com.databricks:spark-csv_2.11:1.5.0
STREAMING_SCRIPT=$CHARGE_TRACKER_HOME/src/spark/cycle_step_analysis.py

tmux new-session -s spark
tmux new-window -t spark
tmux send-keys -t spark:spark 'sudo python '"$SPARK_START"' '"--master $SPARK_MASTER"' '"--packages $SPARK_PACKAGES"' '"$STREAMING_SCRIPT"' ' C-m