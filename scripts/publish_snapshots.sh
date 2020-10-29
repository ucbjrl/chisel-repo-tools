
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

# make sure WORKDIR is a git repo from chisel-release
run_and_check 0.1 $REPOTOOLS/scripts/check_work_dir.sh

run_and_check 3.3 git checkout master && git pull

run_and_check 3.4 git submodule update --init --recursive

run_and_check 3.5 make -f Makefile pull

run_and_check 3.6 echo git add -u

run_and_check 3.7 echo git commit -m "Bump versions"

run_and_check 3.8 echo git push


