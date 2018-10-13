**TODO: ADD LOGO**
ChargeTracker: Near real-time analysis of rechargeable battery systems

## Cluster setup

Create new VPC with associated subnet.
Create new security group for ChargeTracker.
Create new EC2 instance as control node.

From local machine, upload PEM keypair to control node:
```
scp -i <path-to-keypair> <path-to-copy-keypair> ec2-user@<IP-control-node>:/home/ec2-user/.ssh/
```

Clones ChargeTracker and installs dependencies onto control node:
```
# Updates all packages on EC2 AMI 1 instance
sudo yum update
# Installs all dependencies and packages
sudo yum install git tmux python36 python36-debug python36-devel python36-libs python36-pip python36-setuptools python36-test python36-tools python36-virtualenv python-pip
# Craetes "ChargeTracker" directory
mkdir ~/charge_tracker
# Clones "ChargeTracker" git repository
git clone https://github.com/arthurdysart/ChargeTracker.git ~/charge_tracker
# Installs python requirements
sudo pip install -r ~/charge_tracker/util/settings/python_requirements.txt
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