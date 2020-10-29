#

import os
import subprocess


def check_release_dir():
    command_result = subprocess.run(["git", "remote", "-v"], text=True, capture_output=True)
    if command_result.returncode != 0:
        print("You appear to be in the wrong directory")
        print(f"{os.getcwd()} does not appear to be a git repo")
        exit(1)


def checkout_branch(branch_name):
    """checkout specified branch"""

    command_result = subprocess.run(["git", "checkout", branch_name], text=True, capture_output=True)
    if command_result.returncode != 0:
        print(f"git checkout {branch_name} failed")
        exit(1)

    print(f"Now on branch {branch_name}")


def run_pull():
    """runs git pull"""

    command_result = subprocess.run(["git", "pull"], text=True, capture_output=True)
    if command_result.returncode != 0:
        print(f"git pull somehow failed")
        exit(1)

    print(f"git pull complete")


def run_submodule_update_recursive():
    """run git submodule update --init --recursive"""

    command_result = subprocess.run(["git", "submodule", "update", "--init", "--recursive"], text=True,
                                    capture_output=True)
    if command_result.returncode != 0:
        print(f"git submodule update recursive failed")
        exit(1)

    print(f"git submodule update recursive complete")


def run_make_pull():
    """run make pull"""

    command_result = subprocess.run(["make", "pull"], text=True, capture_output=True)
    if command_result.returncode != 0:
        print(f"make pull failed")
        exit(1)

    print(f"make pull complete")


def run_make_clean():
    """run make pull"""

    command_result = subprocess.run(["make", "clean"], text=True, capture_output=True)
    if command_result.returncode != 0:
        print(f"make clean failed")
        exit(1)

    print(f"make clean complete")


def run_make_install():
    """run make install"""

    command_result = subprocess.run(["make", "-j8", "install"], text=True, capture_output=True)
    if command_result.returncode != 0:
        print(f"make install failed")
        exit(1)

    print(f"make install complete")


def run_make_test():
    """run make test"""

    command_result = subprocess.run(["make", "-j8", "test"]) # , text=True, capture_output=True)
    if command_result.returncode != 0:
        print(f"make install failed")
        exit(1)

    print(f"make install complete")
