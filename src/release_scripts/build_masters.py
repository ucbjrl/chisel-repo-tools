"""Updates chisel-release master branch to latest master hash"""

import os
import sys
import getopt

from release_scripts.git_utils.tools import Tools


def usage():
    print(f"Usage: {sys.argv[0]} -repo <repo-dir> [options]")
    print(f"options are:")
    print(f"     --start_step <start_step>")
    print(f"     --stop_step <stop_step>")


def main():
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hr:s:e:",
            ["help", "repo=", "start_step=", "stop_step="]
        )
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    current_dir = ""
    start_step = -1
    stop_step = 1000

    for option, value in opts:
        if option in ("--repo", "-r"):
            current_dir = value
        elif option in ("--start_step", "-s"):
            start_step = value
        elif option in ("--stop_step", "-e"):
            stop_step = value
        else:
            print(f"Unhandled command line option: {option}")
            usage()
            assert False

    print(f"chisel-release directory is {os.getcwd()}")

    if current_dir == "":
        usage()
        exit(1)

    tools = Tools("build_masters")
    tools.set_start_step(start_step)
    tools.set_stop_step(stop_step)

    tools.checkout_branch(1, "master")

    exit(1)

    tools.run_pull(2)

    tools.run_submodule_update_recursive(3)

    tools.run_make_pull(4)

    tools.run_make_clean_install(5)

    tools.run_make_test(6)


if __name__ == "__main__":
    main()
