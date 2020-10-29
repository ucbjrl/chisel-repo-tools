#

import os
import sys

from release_scripts.git_utils import tools

if len(sys.argv) < 2:
    print("Usage: $0 <release repo>")
    exit(1)

current_dir = sys.argv[1]
os.chdir(current_dir)

tools.check_release_dir()

tools.checkout_branch("master")

tools.run_pull()

tools.run_submodule_update_recursive()

tools.run_make_pull()

tools.run_make_clean()
#
#
# # make sure WORKDIR is a git repo from chisel-release
# run_and_check 0.1 $REPOTOOLS/scripts/check_work_dir.sh
#
# run_and_check 3.3 git checkout master && git pull
#
# run_and_check 3.4 git submodule update --init --recursive
#
# run_and_check 3.5 make -f Makefile pull
#
# run_and_check 3.6 echo git add -u
#
# run_and_check 3.7 echo git commit -m "Bump versions"
#
# run_and_check 3.8 echo git push
#
#
