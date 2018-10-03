#!/bin/bash
#
# Automates github repository download.
#
# Template:
# bash pull.sh
# Example:
# bash pull.sh

# Pulls most recent repository version from github
git status
git pull origin master

## END OF FILE