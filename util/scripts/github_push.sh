#!/bin/bash
#
# Automates github push commands
#
# Template:
# bash github_push.sh <commit-message>
# Example:
# bash github_push.sh <commit-message>

# Sets Github commit message
COMMIT_MESSAGE=$1

# Deletes existing Kafka topic
git status
git add --all .
git commit -m "$COMMIT_MESSAGE"
git push origin master

## END OF FILE