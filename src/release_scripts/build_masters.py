#

import os
import sys

print(f"cwd is {os.getcwd()}")
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

tools.run_make_install()

#tools.run_make_test()


