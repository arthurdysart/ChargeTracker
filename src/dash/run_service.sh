#!/bin/bash
#
# From the Dash node, initiate the Dash service and serve GUI dashboard.
#
# Example:
# bash ~/$CHARGE_TRACKER_HOME/src/dash/run_service.sh

CHARGE_TRACKER_HOME=~/charge_tracker

# Starts Dash service
DASH_START=$CHARGE_TRACKER_HOME/src/dash/run_app.py
tmux new-session -s dash
tmux new-window -t dash
tmux send-keys -t dash:dash 'sudo python '"$DASH_START"' ' C-m