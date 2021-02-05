"""This script merges current masters into their corresponding Z.Y.x branches
In general this should only be done before a major release or after creation of next
Z.Y.x
"""

import os
import sys
from argparse import ArgumentParser
from datetime import datetime

from publish_utils.tools import Tools
from publish_utils.step_counter import StepCounter


def main():
    current_date = datetime.now().strftime("%Y%m%d")

    try:
        parser = ArgumentParser()
        parser.add_argument('-r', '--release-dir', dest='release_dir', action='store',
                            help='a directory which is a clone of chisel-release', default=".")
        parser.add_argument('-m', '--major-version', dest='major_version', action='store',
                            help='major number of snapshots being published', required=True)
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
        release_dot_x_version = f"{args.major_version}.x"
        start_step = args.start_step
        stop_step = args.stop_step
        list_only = args.list_only
        counter = StepCounter()

        tools = Tools("merge_master_into_dot_x", release_dir)

        if not list_only:
            print(f"chisel-release directory is {os.getcwd()}")
            print(f"release specified is {release_dot_x_version}")
        else:
            print(f"These are the steps to be executed for the {tools.task_name} script")

        tools.set_start_step(start_step)
        tools.set_stop_step(stop_step)
        tools.set_list_only(list_only)

        #
        # pull in the latest 'master' branches and update the top level
        #
        tools.checkout_branch(counter.next_step(), "master")
        tools.git_pull(counter.next_step())
        tools.run_submodule_update_recursive(counter.next_step())
        tools.run_make_pull(counter.next_step())
        tools.git_add_dash_u(counter.next_step())
        tools.git_commit(counter.next_step(), "Bump master branches")
        tools.git_push(counter.next_step())

        #
        # pull in the latest '.x' branches and update the top level
        #
        tools.checkout_branch(counter.next_step(), release_dot_x_version)
        tools.git_pull(counter.next_step())
        tools.run_submodule_update_recursive(counter.next_step())
        tools.run_make_pull(counter.next_step())
        tools.git_merge_masters_into_dot_x(counter.next_step())
        tools.git_add_dash_u(counter.next_step())
        tools.git_commit(counter.next_step(), "Bump .x branches that just had masters merged into them")
        tools.git_push(counter.next_step())

    except Exception as e:
        print(e)
        sys.exit(2)


if __name__ == "__main__":
    main()
