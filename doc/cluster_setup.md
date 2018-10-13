**TODO: ADD LOGO**
ChargeTracker: Near real-time analysis of rechargeable battery systems

## Cluster setup

Create new VPC with associated subnet. Create new security group for ChargeTracker. Create new EC2 instance as control node.

From local machine, upload PEM keypair to control node:
```
scp -i ~/.ssh/arthurdysart-IAM-keypair.pem ~/Desktop/insight/arthurdysart-IAM-keypair.pem ec2-user@18.232.91.146:/home/ec2-user/.ssh/
```

Update packages and dependencies on control node:
```
# Updates all packages on EC2 AMI 1 instance
sudo yum update
# Lists available packages that have python3 in their name
yum list | grep python3
# Installs git, python 3.6, pip 3.6, and all optional packages
sudo yum install git tmux python36 python36-debug python36-devel python36-libs python36-pip python36-setuptools python36-test python36-tools python36-virtualenv python-pip
# Updates pip
sudo pip-3.6 install --upgrade pip
# Install Python-Kafka library and Cassandra-driver (INSTALL ON KAFKA, SPARK, AND DATABASE MASTER NODES)
sudo pip install python-decouple confluent-kafka pykafka kafka-python cassandra-driver dash==0.28.2 dash-html-components==0.13.2 dash-core-components==0.30.2
```

Install [Insight Pegasus](https://github.com/InsightDataScience/pegasus) service:
```
# Clones "Pegasus" git repositiory
git clone -b feat/ubuntu16 --single-branch ​http://github.com/InsightDataScience/pegasus
# Changes working directory to "/insight/pegasus/"
cd pegasus
# Updates ".bash_profile" with pegasus configuration settings
vi ~/.bash_profile
# Update Bash Profile for Terminal
source ~/.bash_profile
# Returns updated bash profile with peg config settings
peg config
# Initialize new ssh agent to contain Private Keys
eval `ssh-agent -s`
```

For each required technology, spin-up dedicated cluster:
```
# Edits master & worker node parameters, then executes setup
vi ~/insight/pegasus/examples/<technology-name>/master.yml
peg up ~/insight/pegasus/examples/<technology-name>/master.yml
vi ~/insight/pegasus/examples/<technology-name>/workers.yml
peg up ~/insight/pegasus/examples/<technology-name>/workers.yml
# Updates keypair and check cluster addresses
peg fetch <cluster-name>
# Installs ssh capabilities
peg install <cluster-name> ssh
# Installs AWS privileges
peg install <cluster-name> aws
# Installs package dependencies
peg install <cluster-name> environment
```

For each terminal instance, initiate new ssh-agent:
```
# Initialize new ssh agent to contain Private Keys
eval `ssh-agent -s`
# Updates keypair and check cluster addresses
peg fetch <cluster-name>
# Connects to specified cluster node
peg ssh <cluster-name> <node-number>
```