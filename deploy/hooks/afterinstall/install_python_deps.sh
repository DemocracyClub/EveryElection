#!/usr/bin/env bash
set -xeE

# should we delete the env and recreate?
cd /var/www/every_election/code/
uv venv
. .venv/bin/activate
uv sync --group production --no-group dev --no-group cdk
