#!/usr/bin/env bash

set -x
set -e

root=$(cd $(dirname $0)/.. ; pwd)
PY=${PYTHON:-python3}
PIP=${PIP:-pip3}
PIP_INSTALL=${PIP_INSTALL:-pip install}

# run the cmany unit tests
cd $root/test
export PYTHONPATH=$root/src
$PY -m nose -d -v --with-id --nocapture \
    --with-coverage --cover-erase --cover-package=../src --cover-branches \
    $*

exit $?
