#!/bin/bash

EXPECTED_ORIGIN="https://github.com/ucb-bar/chisel-release"

ORIGIN=`git remote -v | head -1 | awk '{print $2}'`

if [ ! $? == 0 ] ; then
  echo "You appear to be in the wrong directory"
  echo `pwd`" does not appear to be a git repo"
  echo "It should be $EXPECTED_ORIGIN"
  exit 1
fi

if [ ! $ORIGIN == $EXPECTED_ORIGIN ] ; then
  echo "You appear to be in the wrong directory"
  echo "This directory: " `pwd`
  echo "has origin $ORIGIN"
  echo "It should be $EXPECTED_ORIGIN"
  exit 1
fi

exit 0

