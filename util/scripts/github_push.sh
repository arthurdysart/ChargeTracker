#!/bin/bash
#
# Automates github repository upload.
#
# Template:
# bash github_push.sh <commit-message>
# Example:
# bash github_push.sh <commit-message>

# Sets Github commit message
COMMIT_MESSAGE=$1

# Sends new repository to github
git status
git add --all .
git commit -m "$COMMIT_MESSAGE"
git push origin master

## END OF FILE