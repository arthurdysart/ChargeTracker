**TODO: ADD LOGO**
ChargeTracker: Near real-time analysis of rechargeable battery systems

## Cluster setup

From local machine, setup new AWS cluster:
1. Create new VPC with associated subnet.
2. Create new security group for ChargeTracker.
3. Create new EC2 instance as control node.

From local machine, upload PEM keypair to control node:
```
scp -i <path-to-keypair> <path-to-copy-keypair> ec2-user@<IP-control-node>:/home/ec2-user/.ssh/
```

From control node, clone ChargeTracker github repository and install dependencies:
```
# Updates all packages on EC2 AMI 1 instance
yum update
yum install git tmux python36 python36-debug python36-devel python36-libs python36-pip python36-setuptools python36-test python36-tools python36-virtualenv python-pip
# Clones "ChargeTracker" github repository
git clone https://github.com/arthurdysart/ChargeTracker.git ~/charge_tracker
# Installs python requirements
pip install -r ~/charge_tracker/util/settings/python_requirements.txt
```

Install [Insight Pegasus](https://github.com/InsightDataScience/pegasus) service. Note AWS acccount, security group, and subnet parameters should be set for your configuration. See Pegasus documentation for more information:
```
# Clones "Pegasus" github repository
git clone -b feat/ubuntu16 --single-branch http://github.com/InsightDataScience/pegasus ~/charge_tracker
# Updates ".bash_profile" with AWS configuration settings
vi ~/.bash_profile
source ~/.bash_profile
# Returns updated bash profile with peg config settings
peg config
# Initialize new ssh agent to contain Private Keys
eval `ssh-agent -s`
```

From the control node, spin-up dedicated technology cluster. Note AWS security group and subnet parameters should be set for your master/worker node configurations. See Pegasus documentation for more information:
```
# Edits master & worker node parameters, then executes setup
vi ~/insight/pegasus/examples/<technology-name>/master.yml
peg up ~/insight/pegasus/examples/<technology-name>/master.yml
vi ~/insight/pegasus/examples/<technology-name>/workers.yml
peg up ~/insight/pegasus/examples/<technology-name>/workers.yml
# Updates keypair and check cluster addresses
peg fetch <cluster-alias>
# Installs capabilities & privileges on all nodes
peg install <cluster-alias> ssh
peg install <cluster-alias> aws
peg install <cluster-alias> environment
# Clones "ChargeTracker" github repository to all nodes
peg sshcmd-cluster <cluster-alias> "sudo git clone https://github.com/arthurdysart/ChargeTracker.git ~/charge_tracker"
```

From the control node, technologies can be installed and started using the following commands:
```
peg install <cluster-alias> <technology-name>
peg service <cluster-alias> <technology-name> start
```

For each terminal instance in the control node, initiate new ssh-agent before connecting to cluster nodes:
```
# Initialize new ssh agent to contain Private Keys
eval `ssh-agent -s`
# Updates keypair and check cluster addresses
peg fetch <cluster-name>
# Connects to specified cluster node
peg ssh <cluster-name> <node-number>
```