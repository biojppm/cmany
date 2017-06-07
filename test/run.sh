#!/usr/bin/env bash

set -x
set -e

cwd=$(cd $(dirname $0) ; pwd)
export PYTHONPATH=$cwd/../src
PY=${PYTHON:-python3}
PIP=${PIP:-pip3}

$PY -m nose -d -v --with-id --nocapture $*

# test that cmany can be installed and ran
cd $cwd/..
if [ -d dist ] ; then
    rm -vf dist/cmany-*
fi
export PATH=$PATH:$HOME/.local/bin
$PY setup.py sdist bdist_wheel
$PIP uninstall cmany || echo ""
$PIP install --user dist/cmany-*.whl
$PIP show -f cmany
cmany h
cmany h quick_tour
$PIP uninstall cmany

exit $?
