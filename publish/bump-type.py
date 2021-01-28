"""
This assumes that the publish_new_release has just been run and now you want to follow with dated snapshots
It will basically just set all the versions and dependencies to dated snapshots and then
publishSigned everything
"""

import os
import sys
import getopt

from publish_utils.tools import Tools
from publish_utils.step_counter import StepCounter


def usage():
    print(f"Usage: {sys.argv[0]} --repo <repo-dir> --release <release-major-number> --bump-type <bump-type> [options]")
    print(f"options are:")
    print(f"     --repo       <repo>          repo most be a clone of chisel-release")
    print(f"     --bump-type  <bump-type>     must be one of the following")
    print(f"                   major          bumps the major number of the release")
    print(f"                   minor          bumps the minor number of the release")
    print(f"                   rc<n>          set release candidate to the number n")
    print(f"                   rc-clear       clears the release candidate number")
    print(f"                   ds             create datestamped snapshot using todays date")
    print(f"                   ds<YYYMMDD>    create datestamped snapshot using date specified in YYYYMMDD format")
    print(f"                   ds-clear       clear date to create undate stamped snapshot")
    print(f"     --start-step <start_step>    (or -s)")
    print(f"     --stop-step  <stop_step>     (or -e)")
    print(f"     --list-only                  (or -l)")
    print(f"")
    print(f"  Note: --release (-m) defines the major of the release being snapshotted, e.g. '3.4'")


def main():
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "lhr:m:s:e:",
            ["help", "repo=", "release=", "bump-type=", "start-step=", "stop-step=", "list-only"]
        )
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    release_dir = ""
    start_step = -1
    stop_step = 1000
    list_only = False
    bump_type = ""
    counter = StepCounter()

    for option, value in opts:
        if option in ("--repo", "-r"):
            release_dir = value
        elif option in ("--bump-type", "-b"):
            bump_type = f"{value}"
        elif option in ("--start-step", "-s"):
            start_step = int(value)
        elif option in ("--stop-step", "-e"):
            stop_step = int(value)
        elif option in ("--list-only", "-l"):
            list_only = True
        elif option in ("--help", "-h"):
            usage()
            exit(1)
        else:
            print(f"Unhandled command line option: {option}")
            usage()
            assert False

    if release_dir == "":
        print(f"Error: both --repo and --release must be specified to run this script")
        usage()
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
            - Then src/release_scripts/tag_release
            - Then run generate snapshots
        """
    )


if __name__ == "__main__":
    main()
