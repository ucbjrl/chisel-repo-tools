#!/bin/bash

#
# This script creates the necessary python virtual environment

python3 -m venv env
source env/bin/activate
pip install pyyaml
