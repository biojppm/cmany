#!/bin/bash

cwd=$(cd $(dirname $0) ; pwd)

if [ "$TRAVIS_OS_NAME" == "linux" ] ; then

    PYTHON=python3

elif [ "$TRAVIS_OS_NAME" == "osx" ] ; then

    eval "$(pyenv init -)"
    PYTHON="python$PY"

else
    echo WTF
fi


export PYTHONPATH=$cwd/src
$PYTHON -m nose -d -v --with-id --nocapture

exit $?
