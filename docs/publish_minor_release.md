# Publishing a Minor release

## Recipe
This recipe presumes that one shell window is used.
In practice, it is probably best to use two windows/tabs.
That way it can be easier to debug steps being run in one
window by looking at logs in the other.
> But you won't have problems like that, will you? Let's hope not.

### SetUp
###Look over the [Publishing Setup](publishing_setup.md) to see if you have most of the
main dependencies available
- Check the sbt environment
- Is gpg installed?

### Look over the [Python Venv Setup](python_venv_setup.md) (VirtualEnvironment)
- How to set up the python enviroment
- Makes sure all necessary python libraries are installed.
- Activate the python you want
```
source ~/.virtualenvs/chisel-repo-tools/bin/activate
```

### Get the release data and tools
- pick a directory to do your work in
```
cd my-release-work-dir
```
- Clone the chisel-release repo, that provides the repo data to be worked on
```
git clone https://github.com/ucb-bar/chisel-release publish-3.4.1
cd publish-3.4.1
export REPO=`pwd`
cd ..
```
- Clone the tools for doing the release work
```
git clone https://github.com/ucb-bar/chisel-repo-tools.git
cd chisel-repo-tools
```
### Export a bunch of things to make life eaiser (and the scripts work)
```
export PYTHONPATH=`pwd`/src
export VERSIONING=`pwd`/src/versioning/versioning.py
export GPG_TTY=$(tty)
```
and perhaps, (still not sure if this helps or is necessary)
```
export PGP_PASSPHRASE='<your pass key>'
export PGP_SECRET='<your secret>'
```

### A Bit More Setup
- Make sure script is present
```
python src/release_scripts/publish_new_release.py   

    Error: both --repo and --release must be specified to run this script
    Usage: src/release_scripts/publish_new_release.py --repo <repo-dir> --release <release-major-number> --bump-type <bump-type> [options]
    options are:
         --repo       <repo>          repo most be a clone of chisel-release
         --release    <release>       release should be major number of release 3.4 implies branch 3.4.x
         --bump-type  <bump-type>     must be one of the following
                       major          bumps the major number of the release
                       minor          bumps the minor number of the release
                       rc<n>          set release candidate to the number n
                       rc-clear       clears the release candidate number
                       ds             create datestamped snapshot using todays date
                       ds<YYYMMDD>    create datestamped snapshot using date specified in YYYYMMDD format
                       ds-clear       clear date to create undate stamped snapshot
         --start-step <start_step>    (or -s)
         --stop-step  <stop_step>      (or -e
         --list-only                  (or -l)
    
      Note: --release (-m) defines the major of the release being snapshotted, e.g. '3.4'
```
  - No args will show standard help info
- List the steps to reinforce what;s going on here
  - Note use of $REPO to point to our chisel-release directory
  - --list-only just shows the steps
```
python src/release_scripts/publish_new_release.py --repo $REPO --release 3.4 --list-only

    chisel-release directory is /Users/chick/Adept/dev/release-generators/chisel-repo-tools
    release specified is 3.4.x
    These are the steps to be executed for the src/release_scripts/publish_new_release.py script
    step   1 checkout_branch
    step   2 run_submodule_update_recursive
    step   3 run_make_pull
    step   4 git_add_dash_u
    step   5 git_commit
    step   6 git_push
    step   7 checkout_branch
    step   8 run_submodule_update_recursive
    step   9 run_make_pull
    step  10 git_add_dash_u
    step  11 git_commit
    step  12 git_push
    step  13 bump_release
    step  14 check_version_updates
    step  15 add_and_commit_submodules
    step  16 git_add_dash_u
    step  17 git_commit
    step  18 merge_dot_x_branches_into_release_branches
    step  19 verify_merge
    step  20 run_make_clean_install
    step  21 run_make_test
    step  22 commit_each_submodule
    step  23 git_add_dash_u
    step  24 git_commit
    step  25 push_submodules
    step  26 git_push
    step  27 publish_signed
    step  28 comment
```
- Run the publish script for real
  - if we need to restart for some reason, --start-step and --stop-step can be used to control execution

```
python src/release_scripts/publish_new_release.py --repo $REPO --release 3.4 --bump-type minor
```

> If any of the steps fail then the script will exit immediately and it will tell you where to look to find the
> output of the failed step. In general the logging from each individual step will be in a 
>
### Close and Publish the release on Sonatype

This is an interactive GUI on the [oss.sonatype.org](https://oss.sonatype.org) website
#### [Instructions to finalize release on sonatype](sonatype_finalize_release.md)

## Finish up

```
python src/release_scripts/tag_new_release.py --repo $REPO
```