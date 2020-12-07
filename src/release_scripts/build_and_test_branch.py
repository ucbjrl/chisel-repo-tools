"""builds and tests the submodules on the current branch of repo"""

import os
import sys
import getopt

from release_scripts.git_utils.tools import Tools
from release_scripts.git_utils.step_counter import StepCounter


def usage():
    print(f"Usage: {sys.argv[0]} --repo <repo-dir> --release <release-major-number> [options]")
    print(f"options are:")
    print(f"     --start-step <start_step>    (or -s)")
    print(f"     --stop-step <stop_step>      (or -e")
    print(f"     --list-only                  (or -l)")
    print(f"")
    print(f"  Note: --release (-m) defines the major of the release being snapshotted, e.g. '3.4'")


def main():
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "lhr:m:s:e:",
            ["help", "repo=", "release=", "start-step=", "stop-step=", "list-only"]
        )
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    release_dir = ""
    start_step = -1
    stop_step = 1000
    list_only = False
    release_version = ""
    counter = StepCounter()

    for option, value in opts:
        if option in ("--repo", "-r"):
            release_dir = value
        elif option in ("--release", "-m"):
            release_version = f"{value}.x"
        elif option in ("--start-step", "-s"):
            start_step = int(value)
        elif option in ("--stop-step", "-e"):
            stop_step = int(value)
        elif option in ("--list-only", "-l"):
            list_only = True
        elif option in ("--help", "-h"):
            usage()
            exit(1)
        else:
            print(f"Unhandled command line option: {option}")
            usage()
            assert False

    tools = Tools("publish_snapshots", release_dir)

    if not list_only:
        if release_dir == "" or release_version == "":
            print(f"Error: both --repo and --release must be specified to run this script")
            usage()
            exit(1)
        else:
            print(f"chisel-release directory is {os.getcwd()}")
            print(f"release specified is {release_version}")
    else:
        print(f"These are the steps to be executed for the {tools.task_name} script")

    tools.set_start_step(start_step)
    tools.set_stop_step(stop_step)
    tools.set_list_only(list_only)

    tools.checkout_branch(counter.next_step(), release_version)

    tools.git_pull(counter.next_step())

    tools.run_submodule_update_recursive(counter.next_step())

    tools.run_make_pull(counter.next_step())

    tools.run_make_clean_install(counter.next_step())

    tools.run_make_test(counter.next_step())

if __name__ == "__main__":
    main()
