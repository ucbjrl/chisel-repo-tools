"""tags release branches"""

import os
import sys
import getopt

from publish_utils.tools import Tools
from publish_utils.step_counter import StepCounter


def usage():
    print(f"Usage: {sys.argv[0]} --repo <repo-dir> --release <Z.Y> [options]")
    print(f"options are:")
    print(f"     --release    <release>       full release number e.g. 3.4.1")
    print(f"     --dry-run")
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
            ["help", "repo=", "release=", "dry-run", "start-step=", "stop-step=", "list-only"]
        )
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    release_dir = ""
    release_version = ""
    start_step = -1
    stop_step = 1000
    list_only = False
    is_dry_run = False
    counter = StepCounter()

    for option, value in opts:
        if option in ("--repo", "-r"):
            release_dir = value
        elif option in ("--release", "-m"):
            release_version = f"{value}"
        elif option == "--dry-run":
            is_dry_run = True
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

    if release_dir == "" or release_version == "":
        print(f"Error: both --repo and --release must be specified to run this script")
        usage()
        exit(1)
    else:
        print(f"chisel-release directory is {os.getcwd()}")

    if list_only:
        print(f"These are the steps to be executed for the {sys.argv[0]} script")

    tools = Tools("tag_new_release", release_dir)

    tools.set_start_step(start_step)
    tools.set_stop_step(stop_step)
    tools.set_list_only(list_only)

    tools.tag_submodules(counter.next_step(), is_dry_run)
    tools.tag_top_level(counter.next_step(), is_dry_run, release_version)

    tools.comment(
        counter.next_step(),
        f"""
        Congratulations your release is published
            - You should probably publish snapshots next
        """
    )


if __name__ == "__main__":
    main()
