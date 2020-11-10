"""publishes a new release"""

import os
import sys
import getopt

from release_scripts.git_utils.tools import Tools
from release_scripts.git_utils.step_counter import StepCounter


def usage():
    print(f"Usage: {sys.argv[0]} --repo <repo-dir> --release <release-major-number> --bump-type <bump-type> [options]")
    print(f"options are:")
    print(f"     --start-step <start_step>    (or -s)")
    print(f"     --stop-step <stop_step>      (or -e")
    print(f"     --list-only                  (or -l)")
    print(f"  bump_type must be in one of the following forms")
    print(f"    bump_max       bumps the major number of the release")
    print(f"    bump_min       bumps the minor number of the release")
    print(f"    rc<n>          set release candidate to the number n")
    print(f"    rc-clear       clears the release candidate number")
    print(f"    ds             create datestamped snapshot using todays date")
    print(f"    ds<YYYMMDD>    create datestamped snapshot using date specified in YYYYMMDD format")
    print(f"    ds-clear       clear date to create undate stamped snapshot")
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
    release_dot_x_version = ""
    release_version = ""
    bump_type = ""
    counter = StepCounter()

    for option, value in opts:
        if option in ("--repo", "-r"):
            release_dir = value
        elif option in ("--release", "-m"):
            release_dot_x_version = f"{value}.x"
            release_version = f"{value}-release"
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
        if release_dir == "" or release_dot_x_version == "":
            print(f"Error: both --repo and --release must be specified to run this script")
            usage()
            exit(1)
        else:
            print(f"chisel-release directory is {os.getcwd()}")
            print(f"release specified is {release_dot_x_version}")
    else:
        print(f"These are the steps to be executed for the {tools.task_name} script")

    tools.set_start_step(start_step)
    tools.set_stop_step(stop_step)
    tools.set_list_only(list_only)

    #
    # pull in the latest '.x' branches and update the top level
    #
    tools.checkout_branch(counter.next_step(), release_dot_x_version)

    tools.run_submodule_update_recursive(counter.next_step())

    tools.run_make_pull(counter.next_step())

    tools.git_add_dash_u(counter.next_step())

    tools.git_commit(counter.next_step(), "Bump .x branches")

    tools.git_push(counter.next_step())

    #
    # pull in the latest '-release' branches and update the top level
    #
    tools.checkout_branch(counter.next_step(), release_dot_x_version)

    tools.run_submodule_update_recursive(counter.next_step())

    tools.run_make_pull(counter.next_step())

    tools.git_add_dash_u(counter.next_step())

    tools.git_commit(counter.next_step(), "Bump .x branches")

    tools.git_push(counter.next_step())

    #
    # Bump the -release branch versions
    #
    tools.verify_merge(counter.next_step())

    tools.run_make_clean_install(counter.next_step())

    tools.run_make_test(counter.next_step())

    tools.git_add_dash_u(counter.next_step())

    tools.git_commit(counter.next_step(), f"Release {release_dot_x_version} top level updated")

    tools.git_push(counter.next_step())


if __name__ == "__main__":
    main()
