#!/bin/bash
set -euxo pipefail

pytest
cd packages/uk-election-timetables
pytest
