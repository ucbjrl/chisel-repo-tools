"""Builds and installs the submodules on the current branch in specified repo"""

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

        Tools.add_standard_cli_arguments(parser)

        args = parser.parse_args()

        release_dir = args.release_dir
        start_step = args.start_step
        stop_step = args.stop_step
        list_only = args.list_only
        counter = StepCounter()

        tools = Tools("build_submodules", release_dir)

        if not list_only:
            if release_dir == "":
                print(f"Error: --repo must be specified to run this script")
                exit(1)
            else:
                print(f"chisel-release directory is {os.getcwd()}")
        else:
            print(f"These are the steps to be executed for the {tools.task_name} script")

        tools.set_start_step(start_step)
        tools.set_stop_step(stop_step)
        tools.set_list_only(list_only)

        tools.run_make_clean_install(counter.next_step())

    except Exception as e:
        print(e)
        sys.exit(2)


if __name__ == "__main__":
    main()
