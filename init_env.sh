#!/bin/bash

#assuming the machine has virtualenv and pip installed
if [ ! -d cache ]
  then
   mkdir cache
fi

virtualenv --no-site-packages venv

export PYTHONPATH=

source venv/bin/activate
pip install --download-cache=cache  yolk nose

pip install --download-cache=cache -r requirements.pip
