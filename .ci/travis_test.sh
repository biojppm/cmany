#!/usr/bin/env bash

cwd=$(cd $(dirname $0) ; pwd)

export PYTHONPATH=$cwd/src

python3 -m nose -d -v --with-id --nocapture

exit $?
