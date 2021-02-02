"""tags release branches"""

import os
import sys
from argparse import ArgumentParser

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
        parser = ArgumentParser()
        parser.add_argument('-r', '--release-dir', dest='release_dir', action='store',
                            help='a directory which is a clone of chisel-release default is "."', default=".")
        parser.add_argument('-rv', '--release-version', dest='release_version', action='store',
                            help='full release number Z.Y.X eg. 3.4.2', required=True)
        parser.add_argument('-d', '--dry-run', dest='is_dry_run', action='store_true',
                            help='if set just shows command that will be called')

        Tools.add_standard_cli_arguments(parser)

        args = parser.parse_args()

        release_dir = args.release_dir
        release_version = args.release_version
        start_step = args.start_step
        stop_step = args.stop_step
        list_only = args.list_only
        is_dry_run = args.is_dry_run
        counter = StepCounter()

        if release_dir == "" or args.release_version == "":
            print(f"Error: both --repo and --release-version must be specified to run this script")
            usage()
            exit(1)
        else:
            print(f"chisel-release directory is {os.getcwd()}")

        if list_only:
            print(f"These are the steps to be executed for the {sys.argv[0]} script")

        tools = Tools("tag_new_release", release_dir)

        cb = tools.get_current_branch(0)
        print(f"current branch {cb}")

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
    except Exception as e:
        print(e)
        sys.exit(2)


if __name__ == "__main__":
    main()
