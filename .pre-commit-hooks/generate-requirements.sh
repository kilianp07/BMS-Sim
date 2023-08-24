#!/bin/bash

# Use pipreqs to generate requirements.txt from your environment and dependencies
pipreqs . --force

# Check if requirements.txt is modified
if git diff --exit-code requirements.txt; then
  echo "requirements.txt is up-to-date"
  exit 0
else
  echo "requirements.txt is outdated, please run 'pipreqs . --force' to update it."
  exit 1
fi
