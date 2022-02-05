#!/usr/bin/env bash

# Logic for subbing commands in the Makefile
case "$1$2" in
  'chiseltest+test') echo '+testOnly -- -l RequiresVcs';;
  *) echo $2;;
esac

