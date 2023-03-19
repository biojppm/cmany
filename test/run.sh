#!/usr/bin/env bash

set -x
set -e

root=$(cd $(dirname $0)/.. ; pwd)
PY=${PYTHON:-python3}

# run the cmany unit tests
cd $root/test
export PYTHONPATH=$root/src
$PY -m pytest --cov=../src --cov-reset -v $*

exit $?
