"""Updates chisel-release master branch to latest master hash"""

import os
import sys

from release_scripts.git_utils.tools import Tools

print(f"chisel-release directory is {os.getcwd()}")

if len(sys.argv) < 2:
    print("Usage: $0 <release repo>")
    exit(1)

current_dir = sys.argv[1]
os.chdir(current_dir)

tools = Tools("build_masters")
tools.set_start_step(11)

tools.checkout_branch(1, "master")

exit(1)

tools.run_pull(2)

tools.run_submodule_update_recursive(3)

tools.run_make_pull(4)

tools.run_make_clean_install(5)

tools.run_make_test(6)


