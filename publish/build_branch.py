"""checks out the desired branch and builds all the submodules"""

import os
import sys
from argparse import ArgumentParser

from publish_utils.tools import Tools
from publish_utils.step_counter import StepCounter


def usage():
    print(f"Usage: {sys.argv[0]} --repo <repo-dir> --branch <repo-dir-branch> [options]")
    print(f"options are:")
    print(f"     --start-step <start_step>    (or -s)")
    print(f"     --stop-step <stop_step>      (or -e")
    print(f"     --list-only                  (or -l)")


def main():
    try:
        parser = ArgumentParser()
        parser.add_argument('-r', '--release', dest='release_dir', action='store',
                            help='a directory which is a clone of chisel-release', required=True)
        parser.add_argument('-br', '--branch', dest='branch', action='store',
                            help='branch to build', required=True)
        parser.add_argument('-b', '--start-step', dest='start_step', type=int, action='store',
                            help='command step to start on',
                            default=1)
        parser.add_argument('-e', '--stop-step', dest='stop_step', type=int, action='store',
                            help='command step to end on',
                            default=10000)
        parser.add_argument('-l', '--list-only', dest='list_only', action='store_true',
                            help='list command step, do not execute', default=False)

        args = parser.parse_args()

        release_dir = args.release_dir
        start_step = args.start_step
        stop_step = args.stop_step
        list_only = args.list_only
        counter = StepCounter()

        tools = Tools("build_branch", release_dir)

        if not list_only:
            print(f"chisel-release directory is {os.getcwd()}")
        else:
            print(f"These are the steps to be executed for the {tools.task_name} script")

        tools.set_start_step(start_step)
        tools.set_stop_step(stop_step)
        tools.set_list_only(list_only)

        tools.checkout_branch(counter.next_step(), "master")

        tools.git_pull(counter.next_step())

        tools.run_submodule_update_recursive(counter.next_step())

        tools.run_make_pull(counter.next_step())

        tools.run_make_install(counter.next_step())

    except Exception as err:
        print(err)
        sys.exit(2)


if __name__ == "__main__":
    main()
