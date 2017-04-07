#!/bin/bash

if [ -z "${PYENV_VERSIONS}" ] ; then
    PYENV_VERSIONS=$(pyenv versions --bare)
fi

sdir=$(cd $(dirname $0) ; pwd)
rdir=$(cd $sdir/.. ; pwd)
stat=0

function show_cmd()
{
    echo -n "$*: "
    $*
}

function mark_failed()
{
    stat=$1
    ver=$2
    stat=$1
    failed="$failed $ver"
}

for v in $PYENV_VERSIONS ; do
    pyenv local $v || exit 1
    show_cmd which python
    show_cmd which pip
    show_cmd pyenv which python
    show_cmd pyenv which pip
    pip install -r $rdir/requirements.txt
    pip install -r $rdir/requirements_test.txt
    $sdir/../test/run.sh $* || mark_failed $? $v
done

if [ $stat == 0 ] ; then
    echo "$0: Successfully ran all tests:"
    for v in $PYENV_VERSIONS ; do
        echo $v
    done
else
    echo "$0: ----- FAILED tests:"
    for v in $failed ; do
        echo $v
    done
fi

exit $stat
