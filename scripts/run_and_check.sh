#!/bin/bash

# run a command and exit on failure
#
function run_and_check() {
  section=$1
  shift
  command=$*

  if $command ; then
    echo "Section $section complete"
  else
    echo "Section $section failed"
    echo "Command: $command"
    exit 1
  fi
}
