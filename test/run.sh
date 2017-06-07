#!/usr/bin/env bash

set -x
set -e

root=$(cd $(dirname $0)/.. ; pwd)
PY=${PYTHON:-python3}
PIP=${PIP:-pip3}
PIP_INSTALL=${PIP_INSTALL:-pip install}

# test that cmany can be installed and ran
cd $root
if [ -d dist ] ; then rm -vf dist/cmany-* ; fi
if [ -d build ] ; then rm -rf build/* ; fi
export PATH=$PATH:$HOME/.local/bin
$PY setup.py sdist bdist_wheel
$PIP uninstall -y cmany || echo ""
$PIP_INSTALL dist/cmany-*.whl
$PIP show -f cmany
cmany h
cmany h quick_tour
$PIP uninstall -y cmany

# run the cmany unit tests
cd test
export PYTHONPATH=$root/src
$PY -m nose -d -v --with-id --nocapture $*

exit $?
