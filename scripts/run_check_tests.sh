#!/bin/bash

#// SPDX-License-Identifier: Apache-2.0

if [ -z "$1" ] ; then
  echo "Usage: $0 <release repo>"
  exit 1
fi

REPOTOOLS=`pwd`
export PATH=$REPOTOOLS/scripts:$REPOTOOLS/src:$PATH

# specify where release work will be done
WORKDIR=$1
cd $WORKDIR

if [ -z "$PYTHONPATH" ] ; then
  export PYTHONPATH=$REPOTOOLS/src
fi

if [ -z "$VERSIONING" ] ; then
  export VERSIONING=$REPOTOOLS/src/versioning/versioning.py
fi

source run_and_check.sh

# check python virtual environment
run_and_check 0.0 python $REPOTOOLS/src/utils/check_virtual_env.py

run_and_check_neg 4.2 grep '\[error\]' run_tests_test.out

run_and_check_neg 4.1 grep -n "Tests:.succeeded.*failed.[1-9]" run_tests_test.out

# run_and_check 4.3 tail -100 run_tests_test.out