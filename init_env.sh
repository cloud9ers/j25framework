#!/bin/bash

#assuming the machine has virtualenv and pip installed

virtualenv --no-site-packages environment

export PYTHONPATH=

pip install -E environment yolk nose

pip install -E environment -r requirements.pip
