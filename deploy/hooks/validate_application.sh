#!/usr/bin/env bash
set -xeuo pipefail

# if either check returns a non-zero exit code, return exit code 1 to
# ensure CodeDeploy recognises the validation failed
systemctl is-active --quiet gunicorn_every_election.service || exit 1
