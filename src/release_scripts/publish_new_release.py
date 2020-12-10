"""publishes a new release"""

import os
import sys
from argparse import ArgumentParser

from release_scripts.git_utils.tools import Tools
from release_scripts.git_utils.step_counter import StepCounter


def main():
    try:
        parser = ArgumentParser()
        parser.add_argument('-r', '--release', dest='release_dir', action='store',
                            help='a directory which is a clone of chisel-release', required=True)
        parser.add_argument('-m', '--major-version', dest='major_version', action='store',
                            help='major number of snapshots being published', required=True)
        parser.add_argument('-bt', '--bump-type', dest='bump_type', action='store', choices=['major', 'minor'],
                            help='Is this a major or a minor release',
                            required=True)
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
        release_version = f"{args.major_version}-release"
        bump_type = args.bump_type
        start_step = args.start_step
        stop_step = args.stop_step
        list_only = args.list_only
        counter = StepCounter()

        print(f"chisel-release directory is {os.getcwd()}")
        print(f"release specified is {release_dot_x_version}")

        if not list_only:
            # this will validate bump_tpe and exit on failure
            Tools.get_versioning_command(bump_type)
        else:
            print(f"These are the steps to be executed for the {sys.argv[0]} script")

        tools = Tools("publish_snapshots", release_dir)

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
        tools.verify_merge(counter.next_step())

        #
        # Test that everything compiles and tests with new release numbers
        #
        tools.run_make_clean_install(counter.next_step())
        tools.run_make_test(counter.next_step())

        #
        # Commit merges
        #
        tools.commit_each_submodule(counter.next_step())
        tools.git_add_dash_u(counter.next_step())
        tools.git_commit(counter.next_step(), f"Release {release_version} top level committed")

        # Publish release
        #
        tools.publish_signed(counter.next_step())

        #
        # Push release, release numbers have been bumped by here
        #
        tools.push_submodules(counter.next_step())
        tools.git_push(counter.next_step())

        tools.comment(
            counter.next_step(),
            f"""
            You are almost done
                - Follow steps in docs/sonatype_finalize_release.md
                - Then src/release_scripts/tag_release
                - Then run generate snapshots
            """
        )
    except Exception as e:
        print(e)
        sys.exit(2)


if __name__ == "__main__":
    main()
