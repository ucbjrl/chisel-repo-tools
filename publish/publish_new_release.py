"""publishes a new release, either major or minor"""

import os
import sys
from argparse import ArgumentParser

from publish_utils.tools import Tools
from publish_utils.step_counter import StepCounter


def make_parser():
    def validate_bump_type(arg):
        # Just check if it parses but return original arg because it is used later
        Tools.get_versioning_command_args(arg)
        return arg

    parser = ArgumentParser()
    parser.add_argument('-r', '--release-dir', dest='release_dir', action='store',
            help='a directory which is a clone of chisel-release default is "."', default=".")
    parser.add_argument('-m', '--major-version', dest='major_version', action='store',
            help='major number of release being bumped', required=True)
    parser.add_argument('-bt', '--bump-type', dest='bump_type', action='store',
            type=validate_bump_type, required=True,
            help='What type of release is this? '
                 '[major, minor, rc<#>, rc-clear, m<#>, ds, ds<YYYYMMDD>, ds-clear]')
    Tools.add_standard_cli_arguments(parser)

    return parser


def main():
    try:
        parser = make_parser()
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

        if list_only:
            print(f"These are the steps to be executed for the {sys.argv[0]} script")

        tools = Tools("publish_new_release", release_dir)

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
        # Merge tracked branches (usually master or .x) in to -release branches
        tools.merge_tracked_branches_into_release_branches(counter.next_step())
        tools.verify_merge(counter.next_step())

        #
        # Test that everything compiles and tests with new release numbers
        #
        tools.run_make_clean(counter.next_step())
        tools.run_make_install(counter.next_step())
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
                - Then publish/tag_release
                - Then run generate snapshots
            """
        )
    except Exception as e:
        print(e)
        sys.exit(2)


if __name__ == "__main__":
    main()
