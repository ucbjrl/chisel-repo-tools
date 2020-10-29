#

import os
import subprocess


def check_release_dir():
    """Look to see if the current working directory is a clone of chisel-release"""

    command_result = subprocess.run(["git", "remote", "-v"], text=True, capture_output=True)
    if command_result.returncode != 0:
        print("You appear to be in the wrong directory")
        print(f"{os.getcwd()} does not appear to be a git repo")
        exit(1)


