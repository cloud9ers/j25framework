#!/bin/bash
export PYTHONPATH=`dirname $0`/..:$PYTHONPATH
python textrunner.py -l INFO -m ".*[Tt]est" --with-cov --cov ../ --cov-report xml --with-xunit --xunit-file report.xml $*
