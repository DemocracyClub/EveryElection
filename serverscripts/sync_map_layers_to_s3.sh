#!/bin/sh
set -e

MAP_DATA_PATH=/var/www/every_election/repo/every_election/data/maps
mkdir -p $MAP_DATA_PATH

manage-py-command export_boundaries --output $MAP_DATA_PATH

aws s3 sync $MAP_DATA_PATH s3://ee.public.data/ee-maps/ --acl public-read --content-type "application/json"
rm $MAP_DATA_PATH/*
