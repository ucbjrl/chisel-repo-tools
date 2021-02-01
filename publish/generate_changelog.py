"""generates change logs for new release"""

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
        parser.add_argument('-r', '--release', dest='release_dir', action='store',
                            help='a directory which is a clone of chisel-release', required=True)
        parser.add_argument('-m', '--major-version', dest='major_version', action='store',
                            help='major number of snapshots being published', required=True)
        parser.add_argument('-d', '--date-range', dest='date_range', action='store',
                            help='set dates to search for PRs, e.g. ">2021-04-01" or "2021-05-01..2021-05-31',
                            default=current_date)
        parser.add_argument('-c', '--clear-db', dest='clear_db', action='store_true',
                            help='clears issues collection from each repo database before downloading', default=False)
        parser.add_argument('-g', '--github-token', dest='github_token', action='store',
                            help='Way to set your github token, will use env var GHRPAT if not set by this',
                            default="")
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
        if args.github_token == "":
            token = os.getenv("GHRPAT")
            if token is None or token == "":
                print(f"You must either set a GHRPAT environment variable or use '--github-token token'")
                print(parser.usage)
        else:
            token = args.github_token
            os.environ['GHRPAT'] = token
        date_range = args.date_range
        clear_db = args.clear_db
        start_step = args.start_step
        stop_step = args.stop_step
        list_only = args.list_only
        counter = StepCounter()

        print(f"chisel-release directory is {os.getcwd()}")
        print(f"release specified is {release_dot_x_version}")

        if list_only:
            print(f"These are the steps to be executed for the {sys.argv[0]} script")

        tools = Tools("generate_changlog", release_dir)

        tools.set_start_step(start_step)
        tools.set_stop_step(stop_step)
        tools.set_list_only(list_only)

        #
        # pull in the latest '.x' branches and update the top level
        #
        tools.checkout_branch(counter.next_step(), release_dot_x_version)
        tools.git_pull(counter.next_step())
        tools.run_submodule_update_recursive(counter.next_step())
        tools.run_submodule_fetch_from_origin(counter.next_step())

        tools.populate_db_with_request_issues(counter.next_step(), date_range, clear_db)
        tools.verify_version_tag(counter.next_step())
        tools.generate_git_log_one_liners(counter.next_step())
        tools.generate_changelog(counter.next_step())

    except Exception as e:
        print(e)
        sys.exit(2)


if __name__ == "__main__":
    main()
