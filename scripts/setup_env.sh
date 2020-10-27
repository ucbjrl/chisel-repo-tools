#!/bin/bash

#
# This script is designed to be sourced to create a proper environment for running release scripts
#
source ~/.virtualenvs/cit3/bin/activate
export PYTHONPATH=/Users/chick/Adept/dev/release-generators/chisel-repo-tools/src
export VERSIONING=/Users/chick/Adept/dev/release-generators/chisel-repo-tools/src/versioning/versioning.py
sys.prefix == sys.base_prefix