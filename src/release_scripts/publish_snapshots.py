"""publishes updates snapshot and publishes them"""

import os
import sys
from argparse import ArgumentParser
from datetime import datetime

from release_scripts.git_utils.tools import Tools
from release_scripts.git_utils.step_counter import StepCounter


def main():
    current_date = datetime.now().strftime("%Y%m%d")

    try:
        parser = ArgumentParser()
        parser.add_argument('-r', '--release', dest='release_dir', action='store',
                            help='a directory which is a clone of chisel-release', required=True)
        parser.add_argument('-m', '--major-version', dest='major_version', action='store',
                            help='major number of snapshots being published', required=True)
        parser.add_argument('-d', '--dated-snapshot', dest='is_dated_snapshot', action='store_true',
                            help='add datestamp to snapshots',
                            default=False)
        parser.add_argument('-o', '--override-date', dest='date_stamp', action='store',
                            help='overrides the date used for dated snapshots, format YYYYMMDD',
                            default=current_date)
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
        release_version = f"{args.major_version}.x"
        start_step = args.start_step
        stop_step = args.stop_step
        list_only = args.list_only
        date_stamp = args.date_stamp
        bump_type = "date-stamped-clear" if not args.is_dated_snapshot else f"ds{date_stamp}"
        counter = StepCounter()

        tools = Tools("publish_snapshots", release_dir)

        if not list_only:
            Tools.get_versioning_command(bump_type)

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
        tools.verify_merge(counter.next_step())

        tools.bump_release(counter.next_step(), bump_type)

        tools.run_make_clean_install(counter.next_step())
        tools.run_make_test(counter.next_step())

        tools.publish_signed(counter.next_step())

        tools.git_add_dash_u(counter.next_step())
        tools.git_commit(counter.next_step(), f"Release {release_version} top level updated")
        tools.git_push(counter.next_step())
    except Exception as e:
        print(e)
        sys.exit(2)


if __name__ == "__main__":
    main()
