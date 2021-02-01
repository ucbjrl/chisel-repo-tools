"""builds and tests the submodules on the current branch of repo"""

import os
import sys
from argparse import ArgumentParser

from publish_utils.tools import Tools
from publish_utils.step_counter import StepCounter


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
        parser = ArgumentParser()
        parser.add_argument('-r', '--release-dir', dest='release_dir', action='store',
                            help='a directory which is a clone of chisel-release', default=".")
        parser.add_argument('-br', '--branch', dest='branch', action='store',
                            help='major number of snapshots being published', required=True)

        Tools.add_standard_cli_arguments(parser)

        args = parser.parse_args()

        release_dir = args.release_dir
        branch = args.branch
        start_step = args.start_step
        stop_step = args.stop_step
        list_only = args.list_only
        counter = StepCounter()

        tools = Tools("build_and_test_branch", release_dir)

        if not list_only:
            if release_dir == "" or branch == "":
                print(f"Error: both --repo and --release must be specified to run this script")
                usage()
                exit(1)
            else:
                print(f"chisel-release directory is {os.getcwd()}")
                print(f"release specified is {branch}")
        else:
            print(f"These are the steps to be executed for the {tools.task_name} script")

        tools.set_start_step(start_step)
        tools.set_stop_step(stop_step)
        tools.set_list_only(list_only)

        tools.checkout_branch(counter.next_step(), branch)

        tools.git_pull(counter.next_step())

        tools.run_submodule_update_recursive(counter.next_step())

        tools.run_make_pull(counter.next_step())

        tools.run_make_clean_install(counter.next_step())

        tools.run_make_test(counter.next_step())

    except Exception as e:
        print(e)
        sys.exit(2)


if __name__ == "__main__":
    main()
