![ChargeTracker: Near real-time analysis of rechargeable battery systems](https://s3.amazonaws.com/arthur-dysart-github-media/chargetracker/full_logo.png)

ChargeTracker: Near real-time analysis of rechargeable battery systems

## Manual Install

When possible, installation via the [quick start guide](../README.md#quick-start) is recommended as the following instructions have been automated using [Insight Pegasus](https://github.com/InsightDataScience/pegasus).

All technologies and their dependencies must be manually installed on each cluster node. Instructions for Cassandra, Kafka, and Spark installation are available via [Insight Data Science: Engineering Ecosystem](https://github.com/InsightDataScience/data-engineering-ecosystem/wiki).

From the Cassandra master node, initiate the Cassandra service (stores calculated metrics):
```
CHARGE_TRACKER_HOME=~/charge_tracker
CASSANDRA_HOME=/usr/local/cassandra

# Copies Cassandra settings file
NEW_SETTINGS=$CHARGE_TRACKER_HOME/util/settings/cassandra/cassandra.yaml
OLD_SETTINGS=$CASSANDRA_HOME/conf/cassandra.yaml
sudo cp $NEW_SETTINGS $OLD_SETTINGS

# Starts Cassandra service
sudo cassandra &

# Creates Cassandra keyspace and table
bash database_reset.sh "battery_data" "all_metrics"
```

From the Kafka master node, initiate the Kafka service (ingests raw measurements):
```
CHARGE_TRACKER_HOME=~/charge_tracker
KAFKA_HOME=/usr/local/kafka

# Copies Kafka settings file
NEW_SETTINGS=$CHARGE_TRACKER_HOME/util/settings/kafka/server.properties
OLD_SETTINGS=$KAFKA_HOME/config/server.properties
sudo cp $NEW_SETTINGS $OLD_SETTINGS

# Starts Kafka service
KAFKA_START=$KAFKA_HOME/bin/kafka-server-start.sh
sudo $KAFKA_START $OLD_SETTINGS &

# Creates Kafka message topic with 6 partitions and 3 replicas
bash topic_reset.sh "battery_data" "6" "3"
```

From the Spark driver node, initiate the Spark Streaming service (calculates battery metrics):
```
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
sudo $SPARK_START --master $SPARK_MASTER --packages $SPARK_PACKAGES $STREAMING_SCRIPT
```

From the Dash node, initiate the Dash service (serves GUI dashboard):
```
CHARGE_TRACKER_HOME=~/charge_tracker

# Starts Dash service
DASH_START=$CHARGE_TRACKER_HOME/src/dash/run_app.py
sudo python $DASH_START
```

From the generator node, initiate the Tmux producer service (publishes raw measurements to Kafka):
```
CHARGE_TRACKER_HOME=~/charge_tracker

# Starts Tmux producer service (100 battery simulators, 100 cycles, 1200 mA current, voltage range 2.0 - 4.5 V)
GENERATOR_START=$CHARGE_TRACKER_HOME/src/tmux/multiple_batteries.sh
bash $GENERATOR_START generate_batteries 100 100 1200 2.0 4.5
```

View real time battery data using Dash GUI dashboard:
```
python -m webbrowser http://mybatteries.live
```