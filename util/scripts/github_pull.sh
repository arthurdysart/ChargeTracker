#!/bin/bash
#
# Automates github repository download.
#
# Template:
# bash github_pull.sh
# Example:
# bash github_pull.sh

# Pulls most recent repository version from github
git status
git pull origin master

## END OF FILE