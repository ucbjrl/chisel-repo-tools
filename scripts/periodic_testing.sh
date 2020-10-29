
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
  export VERSIONING=$PYTHONPATH/versioning/versioning.py
fi

echo "PYTHONPATH IS $PYTHONPATH"

source run_and_check.sh

# check python virtual environment
run_and_check 1.0 python $REPOTOOLS/src/utils/check_virtual_env.py

# make sure WORKDIR is a git repo from chisel-release
run_and_check 2.0 $REPOTOOLS/scripts/check_work_dir.sh

run_and_check 3.0 git checkout master

run_and_check 3.1 git pull

run_and_check 3.2 git submodule update --init --recursive

run_and_check 3.3.0 mkdir stamps

run_and_check 3.3 make -f Makefile pull

run_and_check 4.0 make -j 8 clean | tee run_tests_clean.out

run_and_check 4.1 make -j 8 install | tee run_tests_install.out

run_and_check 4.2 make -j 8 test | tee run_tests_test.out

run_and_check_neg 4.3 grep '\[error\]' run_tests_test.out

run_and_check_neg 4.4 grep -n "Tests:.succeeded.*failed.[1-9]" run_tests_test.out

run_and_check 5.0 git add -u

run_and_check 5.1 git commit -m "Bump versions"

run_and_check 5.2 git push


