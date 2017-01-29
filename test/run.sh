#!/usr/bin/env bash

set -x

cwd=$(cd $(dirname $0) ; pwd)
export PYTHONPATH=$cwd/../src
PY=${PYTHON:-python3}

$PY -m nose -d -v --with-id --nocapture $*

exit $?
