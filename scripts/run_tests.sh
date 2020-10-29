#!/bin/bash

#// SPDX-License-Identifier: Apache-2.0

if [ -z "$1" ] ; then
  echo "Usage: $0 <release repo>"
  exit 1
fi

WORKDIR=$1
shift

if [ -z "$1" ] ; then
  REPOTOOLS=`pwd`
else
  REPOTOOLS=$1
fi

export PATH=$REPOTOOLS/scripts:$REPOTOOLS/src:$PATH

# specify where release work will be done
cd $WORKDIR

if [ -z "$PYTHONPATH" ] ; then
  export PYTHONPATH=$REPOTOOLS/src
fi

if [ -z "$VERSIONING" ] ; then
  export VERSIONING=$REPOTOOLS/src/versioning/versioning.py
fi

source run_and_check.sh

# check python virtual environment
# run_and_check 0.0 python $REPOTOOLS/src/utils/check_virtual_env.py

# run_and_check 3.1 make -j 8 clean | tee run_tests_clean.out

# run_and_check 3.2 make -j 8 install | tee run_tests_install.out

# run_and_check 3.3 make -j 8 test | tee run_tests_test.out


