"""
This assumes that the publish_new_release has just been run and now you want to follow with dated snapshots
It will basically just set all the versions and dependencies to dated snapshots and then
publishSigned everything
"""

import os
import sys
from argparse import ArgumentParser

from publish_utils.tools import Tools
from publish_utils.step_counter import StepCounter


def main():
    try:
        parser = ArgumentParser()
        parser.add_argument('-r', '--release-dir', dest='release_dir', action='store',
                            help='a directory which is a clone of chisel-release default is "."', default=".")
        parser.add_argument('-bt', '--bump-type', dest='bump_type', action='store', choices=['major', 'minor'],
                            help='Is this a major or a minor release',
                            required=True)
        Tools.add_standard_cli_arguments(parser)

        args = parser.parse_args()

        release_dir = args.release_dir
        bump_type = args.bump_type
        start_step = args.start_step
        stop_step = args.stop_step
        list_only = args.list_only
        counter = StepCounter()

        if release_dir == "":
            print(f"Error: both --repo and --release must be specified to run this script")
            parser.print_help()
            exit(1)
        else:
            print(f"chisel-release directory is {os.getcwd()}")

        if not list_only:
            # this will validate bump_tpe and exit on failure
            Tools.get_versioning_command(bump_type)
        else:
            print(f"These are the steps to be executed for the {sys.argv[0]} script")

        tools = Tools("set_dated_snapshots", release_dir)

        tools.set_start_step(start_step)
        tools.set_stop_step(stop_step)
        tools.set_list_only(list_only)

        #
        # Change repo's release versions and references
        # according to the 'bumptype'
        #
        tools.bump_release(counter.next_step(), bump_type)
        tools.check_version_updates(counter.next_step())
        tools.publish_signed(counter.next_step())

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
