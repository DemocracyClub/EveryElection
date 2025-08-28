#!/usr/bin/env bash
set -xeE

cd /var/www/every_election/code/deploy/tippecanoe
make
make clean
