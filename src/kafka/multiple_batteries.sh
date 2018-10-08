#!/bin/bash
#
# From generator node, creates TMUX windows, each generating battery data as a 
# kafka producer. As battery simulations, TMUX windows publish generated data
# to specified kafka cluster at specified topic.
#
# Template:
# bash multiple_batteries.sh <TMUX-session-name> <number-batteries>
# Example:
# bash multiple_batteries.sh two_batteries 2

# Imports simulation parameters from standard input
TMUX_SESSION_NAME=$1
NUMBER_BATTERIES=$2

# Iteratively create TMUX windows for each battery & corresponding ID number
tmux new-session -s $TMUX_SESSION_NAME
for BATTERY_ID in `seq 1 $NUMBER_BATTERIES`;
do
    echo "Battery ID# $BATTERY_ID ..."
    tmux new-window -t $BATTERY_ID
    tmux send-keys -t $TMUX_SESSION_NAME:$BATTERY_ID 'python battery_python-kafka.py '"$BATTERY_ID"'' C-m
done