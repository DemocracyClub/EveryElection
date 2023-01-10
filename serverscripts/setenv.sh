#!/usr/bin/env bash

# With thanks to https://zwbetz.com/set-environment-variables-in-your-bash-shell-from-a-env-file-version-2/

# Show env vars
grep -v '^#' .env

# Export env vars
set -o allexport
source $1
set +o allexport
