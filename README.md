**TODO: ADD LOGO**

ChargeTracker: Near real-time analysis of rechargeable battery systems

ChargeTracker monitors battery systems containing over 100 independent battery cells. Every 30 seconds, each battery's performance metrics are calculated from raw sensor measurements. Through its GUI dashboard, ChargeTracker aggreagates these metrics by meaningful metadata to enable: (1) comparision across battery groups, and (2) identification of inaccurate outliers.

## Navigation
1. [ABOUT](#about)
2. [DESIGN](#engineering-design)
3. [QUICK START](#quick-start)
4. [CREDITS](#credits)
5. [DEMO](http://mybatteries.live)

## About
ChargeTracker addresses the battery community's need for automated electrochemical analysis and monitoring. Today, battery analysis is inefficient and tedious: raw sensor measurements are retrieved by physical download onto flashdrives, then analyzed using commercial spreadsheet software. ChargeTracker automates this procedure across multiple batteries, permitting battery technicians, engineers, and researchers to focus on more significant tasks and company activities. In this context, ChargeTracker is designed to accelerate team producivitity, technologic progress, and scientific discovery.

ChargeTracker's MapReduce tasks transform raw sensor measurements (i.e., voltage, current, and time) into meaningful battery metrics (total energy and capacity). Analyzed battery data is grouped according to specified metadata (e.g., cathode material W, X, Y, or Z) and displayed on the [live GUI dashboard](http://mybatteries.live), refreshed every 30 seconds:

**TODO: SHOW DASHBOARD IN ACTION**

Below the dashboard, constituent batteries for each group are tabulated and ordered by standard deviation. Outliers are identified by excessive standard deviation from the mean performance value:

**TODO: SHOW TABLE IN ACTION**

ChargeTracker version 1.0 is built on Python 2.7 and processes ca. 2,500 messages per second.

## Engineering Design
ChargeTracker is a streaming analysis pipeline built on 5 open-source technologies:

**TODO: SHOW TABLE IN ACTION**

Each tracked battery publishes raw measurements to the [Apache Kafka] service (into 1 kafka topic, 3 partitions). These raw measurements are consumed by the [Spark Streaming](https://spark.apache.org/streaming/) service and transformed into meaningful metrics via RDD MapReduce tasks. Analyzed results are stored and organized in the [Apache Cassandra](http://cassandra.apache.org/) database service according to partition keys `chemistry` and `test_type` and clustering key `cycle: decending`. The [Dash](https://dash.plot.ly/introduction) service queries the database and refreshes the interactive GUI dashboard every 30 seconds. To optimize throughput, cluster nodes are allocated to services as follows:

| Technology             | Nodes | Purpose                                                                          |
|------------------------|-------|----------------------------------------------------------------------------------|
| Apache Kafka           |   4   | Ingests raw measurements into 1 Kafka topic across 3 partitions (4 brokers)      |
| Apache Spark Streaming |   4   | Transforms raw measurements into battery metrics (1 driver, 3 workers)           |
| Apache Cassandra       |   3   | Partitions analyzed metrics by battery group, clusters by number of (dis)charges |
| Plotly Dash            |   1   | Displays aggregate battery metrics in near real-time GUI                         |
| Insight Pegasus        |   1   | Automates deployment of AWS EC2 instances (1 control node)                       |

The Spark Streaming service executes MapReduce tasks across 3 worker nodes. To optimize data input, the Kafka service's topic is organized into 6 partitions: 2 partitions are fed into each Spark Streaming worker node. The Cassandra service is distributed across an odd number of nodes to enable majority voting, in the case of network downtime, as part of the gossip protcol:

**TODO: SHOW TASK PARALLELIZATION**

## Quick Start
ChargeTracker is executed on a multi-node cluster. Deployment via [Insight Pegasus](https://github.com/InsightDataScience/pegasus) on [AWS Cloud EC2](https://aws.amazon.com/ec2/) is recommended. The project documentation includes detailed instructions for [cluster setup](doc/cluster_setup.md) and [manual installation](doc/manual_install.md).

From control node, initiate all cluster services using [Insight Pegasus](https://github.com/InsightDataScience/pegasus):
```
CHARGE_TRACKER_HOME=~/charge_tracker
# Starts Cassandra service
peg fetch <cassandra-cluster-alias>
peg sshcmd-node <cassandra-cluster-alias> 1 "sudo bash $CHARGE_TRACKER_HOME/src/cassandra/start_service.sh"
# Starts Kafka service
peg fetch <kafka-cluster-alias>
peg sshcmd-node <kafka-cluster-alias> 1 "sudo bash $CHARGE_TRACKER_HOME/src/kafka/start_service.sh"
# Starts Spark service
peg fetch <spark-cluster-alias>
peg sshcmd-node <spark-cluster-alias> 1 "sudo bash $CHARGE_TRACKER_HOME/src/spark/start_service.sh"
# Starts Dash service
peg fetch <dash-cluster-alias>
peg sshcmd-node <dash-cluster-alias> 1 "sudo bash $CHARGE_TRACKER_HOME/src/dash/start_service.sh"
# Starts Tmux multi-producer service
peg fetch <tmux-cluster-alias>
peg sshcmd-node <tmux-cluster-alias> 1 "sudo bash $CHARGE_TRACKER_HOME/src/tmux/start_service.sh"
```

From local computer, open the live GUI dashboard:
```
python -m webbrowser http://mybatteries.live
```


## Credits
ChargeTracker was developed by Arthur Dysart, inspired by automation needs in the battery research community. This project was created as part of the [2018 Insight Data Engineering Fellowship](https://www.insightdataengineering.com/) program.