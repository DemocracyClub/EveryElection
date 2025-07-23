#!/usr/bin/env bash
set -xeuo pipefail

# if either check returns a non-zero exit code, return exit code 1 to
# ensure CodeDeploy recognises the validation failed
systemctl is-active --quiet every_election_gunicorn.service || exit 1
