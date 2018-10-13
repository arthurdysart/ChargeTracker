**TODO: ADD LOGO**

ChargeTracker: Near real-time analysis of rechargeable battery systems

ChargeTracker monitors battery systems containing over 100 independent battery cells. Every 30 seconds, each battery's performance metrics (e.g., total energy and capacity) are calculated from raw sensor measurements (voltage, current, and time). Through its GUI dashboard, ChargeTracker aggreagates these metrics by metadata to enable: (1) comparision across battery groups, and (2) identification of inaccurate outliers.

## Navigation
1. [ABOUT](README.md#About)
2. [DESIGN](README.md#Engineering-Design)
3. [INSTALL](README.md#Install)
4. [CREDITS](README.md#Credits)
5. [DEMO](http://mybatteries.live)

## About
ChargeTracker addresses the battery community's need for automated electrochemical analysis and monitoring. Today, battery analysis is inefficient and tedious: raw sensor measurements are retrieved by physical download onto flashdrives, then analyzed using commercial spreadsheet software. ChargeTracker automates this procedure across multiple batteries, permitting battery technicians, engineers, and researchers to focus on more significant tasks and company activities. In this context, ChargeTracker is designed to accelerate team producivitity, technologic progress, and scientific discovery.

ChargeTracker version 1.0 processes 2,500 messages per second (across 100 independent batteries) and reports aggreagated battery data. This project is built with Python and requires the following technologies:

**TODO: PICTURE OF TECHNOLOGIES**


## Engineering Design
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


## Install
ChargeTracker is executed on a multi-node cluster using AWS EC2 instances. Deployment via [Insight Pegasus](https://github.com/InsightDataScience/pegasus) is recommended and outlined below. Detailed instructions are available in project documentation `\doc\manual_install.md`.

From control node, initiate all cluster services using [Insight Pegasus](https://github.com/InsightDataScience/pegasus):
```
# Starts Cassandra service
peg sshcmd-cluster <cassandra-cluster-alias> "sudo bash $CHARGE_TRACKER_HOME/src/cassandra/start_service.sh"
# Starts Kafka service
peg sshcmd-cluster <kafka-cluster-alias> "sudo bash $CHARGE_TRACKER_HOME/src/kafka/start_service.sh"
# Starts Spark service
peg sshcmd-cluster <spark-cluster-alias> "sudo bash $CHARGE_TRACKER_HOME/src/spark/start_service.sh"
# Starts Dash service
peg sshcmd-cluster <dash-cluster-alias> "sudo bash $CHARGE_TRACKER_HOME/src/dash/start_service.sh"
# Starts Tmux multi-producer service
peg sshcmd-cluster <tmux-cluster-alias> "sudo bash $CHARGE_TRACKER_HOME/src/tmux/start_service.sh"
```

From local computer, open the live GUI dashboard:
```
python -m webbrowser http://mybatteries.live
```


## Credits
ChargeTracker was developed by Arthur Dysart, inspired by automation needs in the battery research community. This project was created as part of the 2018 Insight Data Engineering Fellowship program.