#!/bin/bash -x

# https://docs.travis-ci.com/user/multi-os/

set -e
set -x

echo "TRAVIS_OS_NAME=$TRAVIS_OS_NAME"

if [ "$TRAVIS_OS_NAME" == "linux" ] ; then

    sudo apt-get update
    sudo apt-get install -y \
         python3-pip \
         python3-dev \
         cmake \
         build-essential \
         qemu-system \
         gcc-arm-linux-gnueabihf \
         g++-arm-linux-gnueabihf \
         binutils-arm-linux-gnueabihf \
         #gcc-mips-linux-gnu \
         #g++-mips-linux-gnu \
         #binutils-mips-linux-gnu \
         #gcc-mipsel-linux-gnu \
         #g++-mipsel-linux-gnu \
         #binutils-mipsel-linux-gnu

    PYTHON=python3
    PIP=pip3
    ARM_ABI=1

elif [ "$TRAVIS_OS_NAME" == "osx" ] ; then

    brew update
    #brew install cmake

    #brew install pyenv
    brew upgrade pyenv
    pyenv versions
    pyenv install --list
    pyenv install $PYENV
    pyenv versions
    which python
    python -V
    pyenv local $PYENV
    pyenv versions
    eval "$(pyenv init -)"
    which python
    python -V

    PYTHON=python3
    PIP=pip3
    ARM_ABI=0

fi

cmake --version
cmake --help
which cc
cc --version
which c++
c++ --version
which g++
(g++ -dumpversion ; g++ --version)
which clang++
(clang++ -dumpversion ; clang++ --version)

which $PYTHON
$PYTHON -V

which $PIP
$PIP -V

$PIP install --upgrade setuptools
$PIP install --upgrade pip

cat requirements.txt
$PIP install -r requirements.txt .

cat requirements_test.txt
$PIP install -r requirements_test.txt .

# https://github.com/codecov/codecov-python
# CODECOV_TOKEN="40f841c8-b4a7-4186-9055-dfcd09ed842a"
$PIP install codecov

exit 0
