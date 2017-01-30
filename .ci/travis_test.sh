#!/bin/bash


if [ "$TRAVIS_OS_NAME" == "linux" ] ; then

    export PYTHON=python3

elif [ "$TRAVIS_OS_NAME" == "osx" ] ; then

    eval "$(pyenv init -)"
    export PYTHON="python$PY"
    pyenv local $PYENV

fi

sdir=$(cd $(dirname $0) ; pwd)
$sdir/../test/run.sh $*

exit $?
