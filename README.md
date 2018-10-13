<ADD LOGO>
ChargeTracker: Near real-time analysis of rechargeable battery systems

ChargeTracker monitors battery systems containing over 100 independent battery cells. ChargeTracker's GUI dashboard reports aggreagated battery metrics to enable: (1) comparision across battery groups, and (2) identification of inaccurate outliers. Every 30 seconds, battery metrics (e.g., total energy and capacity) are derived from raw sensor measurements (voltage, current, and time) for each tracked battery cell.

## Navigation
1. [ABOUT](README.md#About)
2. [DESIGN](README.md#Design)
2. [INSTALL](README.md#Quick-start-guide)
4. [FAQ](README.md#Remarks)
6. [CREDITS](README.md#Credits)


## About ChargeTracker
ChargeTracker addresses the modern need for real-time battery monitoring and analysis. Today, battery analysis is inefficient and tedious: raw sensor measurements are physically downloaded onto flashdrives, then analyzed using commercial spreadsheet software. ChargeTracker automates this procedure across multiple batteries, permitting battery technicians, engineers, and researchers to focus on more significant tasks and spending time with loved ones. In this context, ChargeTracker is designed to accelerate team producivitity, technologic progress, and scientific discovery.

ChargeTracker is built with Python and requires the following technologies:

<PICTURE OF TECHNOLOGIES>

ChargeTracker version 1.0 processes 2,500 messages per second (across 100 independent batteries) and reports aggreagated battery data.


## Designing ChargeTracker
ChargeTracker is a streaming analysis pipeline built on 5 open-source technologies:

| Technology             | Nodes | Purpose                                                                      |
|------------------------|-------|------------------------------------------------------------------------------|
| Apache Kafka           |   4   | Ingests measurements into 1 Kafka topic with 3 partitions (4 brokers).       |
| Apache Spark Streaming |   4   | Executes MapReduce tasks (1 driver, 3 workers).                              |
| Apache Cassandra       |   3   | Partitions stored data by battery group; clusters by number of (dis)charges. |
| Plotly Dash            |   1   | Displays aggregate battery metrics in near real-time GUI.                    |
| Insight Pegasus        |   1   | Automates deployment of AWS EC2 instances (1 control node).                  |

<SHORT KAFKA DESCRIPTION>

<SHORT SPARK DESCRIPTION>

<SHORT CASSNANDRA DESCRIPTION>

<SHORT DASH DESCRIPTION>

<SHORT PEGASUS DESCRIPTION>


## Install ChargeTracker
ChargeTracker is executed on a multi-node cluster using AWS EC2 instances. Deployment via Pegasus (Insight Data Science) is recommended and outlined below. Detailed installation instructions are available in <LOCATION>.

<TBA PEGASUS QUICK INSTRUCTIONS>


## Credits
ChargeTracker was developed by Arthur Dysart, inspired by automation needs in the experimental battery research community. This project was created as part of the 2018 Insight Data Engineering Fellowship program.