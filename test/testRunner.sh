#!/bin/bash
VARS=`dirname $0`/../../3rdparty/build/vars.sh
if [ ! -f "$VARS" ]; then
    echo "You didn't build the c9_3rdparty project correctly, cannot find $VARS"
    exit 1
fi
source $VARS
export PYTHONPATH=`dirname $0`/..:$PYTHONPATH
python runner.py $*
