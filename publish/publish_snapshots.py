"""publishes updates snapshot and publishes them"""

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
        parser.add_argument('-d', '--dated-snapshot', dest='is_dated_snapshot', action='store_true',
                            help="add today's date asdatestamp to snapshots",
                            default=False)
        parser.add_argument('-o', '--override-date', dest='date_stamp', action='store',
                            help='overrides the date used for dated snapshots, format YYYYMMDD',
                            default=current_date)
        Tools.add_standard_cli_arguments(parser)

        args = parser.parse_args()

        release_dir = args.release_dir
        release_dot_x_version = f"{args.major_version}.x"
        release_version = f"{args.major_version}-release"
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
        tools.git_pull(counter.next_step())
        tools.run_submodule_update_recursive(counter.next_step())
        tools.run_make_pull(counter.next_step())
        tools.git_add_dash_u(counter.next_step())
        tools.git_commit(counter.next_step(), "Bump .x branches")
        tools.git_push(counter.next_step())

        #
        # pull in the latest '-release' branches and update the top level
        #
        tools.checkout_branch(counter.next_step(), release_version)
        tools.git_pull(counter.next_step())
        tools.run_submodule_update_recursive(counter.next_step())
        tools.run_make_pull(counter.next_step())
        tools.git_add_dash_u(counter.next_step())
        tools.git_commit(counter.next_step(), "Bump -release versions")
        tools.git_push(counter.next_step())

        #
        # Change repo's release versions and references
        # according to the 'bumptype'
        #
        tools.bump_release(counter.next_step(), bump_type)
        tools.check_version_updates(counter.next_step())
        tools.add_and_commit_submodules(counter.next_step())
        tools.git_add_dash_u(counter.next_step())
        tools.git_commit(counter.next_step(), "Bump new -release versions")

        #
        # Merge .x branches in to -release branches
        tools.merge_dot_x_branches_into_release_branches(counter.next_step())
        # TODO: It is not unusual for this step to give errors on rocket, template and tutorials, fix this
        tools.verify_merge(counter.next_step())

        tools.run_make_clean_install(counter.next_step())
        tools.run_make_test(counter.next_step())

        #
        # Commit merges
        #
        tools.commit_each_submodule(counter.next_step())
        tools.git_add_dash_u(counter.next_step())
        tools.git_commit(counter.next_step(), f"Release {release_version} top level committed")

        # TODO: This step will typically require a password to be entered in terminal window, fix this
        tools.publish_signed(counter.next_step())

        #
        # Push release, release numbers have been bumped by here
        #
        tools.push_submodules(counter.next_step())
        tools.git_push(counter.next_step())

    except Exception as e:
        print(e)
        sys.exit(2)


if __name__ == "__main__":
    main()
