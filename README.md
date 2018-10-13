**TODO: ADD LOGO**

ChargeTracker: Near real-time analysis of rechargeable battery systems

ChargeTracker monitors battery systems containing over 100 independent battery cells. Every 30 seconds, battery metrics (e.g., total energy and capacity) are calculated from raw sensor measurements (voltage, current, and time) for each battery. Through its GUI dashboard, ChargeTracker reports aggreagate battery metrics that enable: (1) comparision across meaningful groupings, and (2) identification of inaccurate outliers.

## Navigation
1. [ABOUT](README.md#About-ChargeTracker)
2. [DESIGN](README.md#Design-of-ChargeTracker)
3. [INSTALL](README.md#Install-ChargeTracker)
4. [CREDITS](README.md#Credits)
5. [DEMO](http://mybatteries.live)

## About ChargeTracker
ChargeTracker addresses the battery community's need for automated electrochemical analysis and monitoring. Today, battery analysis is inefficient and tedious: raw sensor measurements are retrieved by physical download onto flashdrives, then analyzed using commercial spreadsheet software. ChargeTracker automates this procedure across multiple batteries, permitting battery technicians, engineers, and researchers to focus on more significant tasks and company activities. In this context, ChargeTracker is designed to accelerate team producivitity, technologic progress, and scientific discovery.

ChargeTracker version 1.0 processes 2,500 messages per second (across 100 independent batteries) and reports aggreagated battery data. This project is built with Python and requires the following technologies:

**TODO: PICTURE OF TECHNOLOGIES**


## Engineering ChargeTracker
ChargeTracker is a streaming analysis pipeline built on 5 open-source technologies:

| Technology             | Nodes | Purpose                                                                          |
|------------------------|-------|----------------------------------------------------------------------------------|
| Apache Kafka           |   4   | Ingests raw measurements into 1 Kafka topic across 3 partitions (4 brokers)      |
| Apache Spark Streaming |   4   | Transforms raw measurements into battery metrics (1 driver, 3 workers)           |
| Apache Cassandra       |   3   | Partitions analyzed metrics by battery group, clusters by number of (dis)charges |
| Plotly Dash            |   1   | Displays aggregate battery metrics in near real-time GUI                         |
| Insight Pegasus        |   1   | Automates deployment of AWS EC2 instances (1 control node)                       |

Raw measurements Per-second Apache Kafka constitues an organized 

**TODO:SHORT SPARK DESCRIPTION**

**TODO:SHORT CASSNANDRA DESCRIPTION**

**TODO:SHORT DASH DESCRIPTION**

**TODO:SHORT PEGASUS DESCRIPTION**


## Install ChargeTracker
ChargeTracker is executed on a multi-node cluster using AWS EC2 instances. Deployment via Insight Pegasus is recommended and outlined below. Detailed instructions are available in project documentation `\doc\README.md`.

From the Cassandra node, initiate the Cassandra service (stores calculated metrics):
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
# Creates Kafka message topic with 3 partitions and 3 replicas
bash topic_reset.sh "battery_data" "3" "3"
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
# Starts Tmux producer service with 100 producers (100 cycles, 1200 mA current, voltage range 2.0 - 4.5 V)
GENERATOR_START=$CHARGE_TRACKER_HOME/src/tmux/multiple_batteries.sh
bash $GENERATOR_START generate_batteries 100 100 1200 2.0 4.5
```

View real time battery data using Dash GUI dashboard:
```
xdg-open http://mybatteries.live
```

## Credits
ChargeTracker was developed by Arthur Dysart, inspired by automation needs in the battery research community. This project was created as part of the 2018 Insight Data Engineering Fellowship program.