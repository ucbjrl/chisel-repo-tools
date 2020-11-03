"""Updates chisel-release master branch to latest master hash"""

import os
import sys
import getopt

from release_scripts.git_utils.tools import Tools


def usage():
    print(f"Usage: {sys.argv[0]} -repo <repo-dir> [options]")
    print(f"options are:")
    print(f"     --start-step <start_step>    (or -s)")
    print(f"     --stop-step <stop_step>      (or -e")
    print(f"     --list-only                  (or -l)")


def main():
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "lhr:s:e:",
            ["help", "repo=", "start-step=", "stop-step=", "list-only"]
        )
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    current_dir = ""
    start_step = -1
    stop_step = 1000
    list_only = False

    for option, value in opts:
        if option in ("--repo", "-r"):
            current_dir = value
        elif option in ("--start-step", "-s"):
            start_step = int(value)
        elif option in ("--stop-step", "-e"):
            stop_step = int(value)
        elif option in ("--list-only", "-l"):
            list_only = True
        else:
            print(f"Unhandled command line option: {option}")
            usage()
            assert False

    print(f"chisel-release directory is {os.getcwd()}")

    if current_dir == "":
        usage()
        exit(1)

    os.chdir(current_dir)

    tools = Tools("build_masters")
    tools.set_start_step(start_step)
    tools.set_stop_step(stop_step)
    tools.set_list_only(list_only)

    tools.checkout_branch(1, "master")

    tools.git_pull(2)

    tools.run_submodule_update_recursive(3)

    tools.run_make_pull(4)

    tools.run_make_clean_install(5)

    tools.run_make_test(6)

    tools.git_add(7)

    tools.git_commit(8, "Bump master branches")


if __name__ == "__main__":
    main()
