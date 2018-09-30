#!/bin/bash
IP_ADDR=$1
NUM_SPAWNS=$2
SESSION=$3
tmux new-session -s $SESSION
for ID in `seq 1 $NUM_SPAWNS`;
do
    echo $ID
    tmux new-window -t $ID
    tmux send-keys -t $SESSION:$ID 'python kafka_producer.py '"$IP_ADDR"' '"$ID"'' C-m
done