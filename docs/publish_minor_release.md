# Publishing a Minor release

## Assumptions

First step is to pick a work directory. Can be anything you like, e.g. `~/chisel-publishing`

### SetUp

### Look over the [Publishing Setup](publishing_setup.md) to see if you have most of the

main dependencies available

### Look over the [Python Venv Setup](python_venv_setup.md) (VirtualEnvironment)

- How to set up the python environment
- Makes sure all necessary python libraries are installed.
- Activate the python you want

```
source ~/.virtualenvs/chisel-repo-tools/bin/activate
```

#### Clone chisel-repo-tools

```
git clone https://github.com/ucb-bar/chisel-repo-tools.git
cd chisel-repo-tools
export PYTHONPATH=`pwd`/src
export VERSIONING=$PYTHONPATH/versioning/versioning.py
cd ..
```

#### Check your environment

- Check the sbt environment
- Is gpg installed?
- Is your the env var GPG_TTY set `export GPG_TTY=$(tty)`
- Is your env var GHRPAT set `export GHRPAT=<your >`
- Is your env var PYTHONPATH set `export PYTHONPATH=<path-to-chisel-repo-tools-clone>/src`
- Is your env var VERSIONING set `export VERSIONING=$PYTHONPATH/versioning/versioning.py`

```
export PGP_PASSPHRASE='<your pass key>'
export PGP_SECRET='<your secret>'
```

### Get the release data and tools

Make sure you are now in the work directoy discussed in *Assumptions* (`~/chisel-publishing`)
And let's assume you are trying to publish the next minor release after 3.4.4 which will be 3.4.5

- Clone the chisel-release repo, that provides the repo data to be worked on

```
git clone https://github.com/ucb-bar/chisel-release publish-3.4.5
cd publish-3.4.5
```

and perhaps, (still not sure if this helps or is necessary)

### A Bit More Setup
- Make sure script is present

```
python publish/publish_new_release.py   

usage: publish_new_release.py [-h] [-r RELEASE_DIR] -m MAJOR_VERSION -bt
                              {major,minor} [-b START_STEP] [-e STOP_STEP] [-l]

optional arguments:
  -h, --help            show this help message and exit
  -r RELEASE_DIR, --release-dir RELEASE_DIR
                        a directory which is a clone of chisel-release default
                        is "."
  -m MAJOR_VERSION, --major-version MAJOR_VERSION
                        major number of release being bumped
  -bt {major,minor}, --bump-type {major,minor}
                        Is this a major or a minor release
  -b START_STEP, --start-step START_STEP
                        command step to start on
  -e STOP_STEP, --stop-step STOP_STEP
                        command step to end on
  -l, --list-only       just list command steps, do not execute
    
      Note: --release (-m) defines the major of the release being snapshotted, e.g. '3.4'
```
  - No args will show standard help info
- List the steps to reinforce what;s going on here
  - Note use of $REPO to point to our chisel-release directory
  - --list-only just shows the steps
```
python publish/publish_new_release.py --repo $REPO --release 3.4 --list-only

    chisel-release directory is /Users/chick/Adept/dev/release-generators/chisel-repo-tools
    release specified is 3.4.x
    These are the steps to be executed for the publish/publish_new_release.py script
    step   1 checkout_branch
    step   2 git_pull
    step   3 run_submodule_update_recursive
    step   4 run_make_pull
    step   5 git_add_dash_u
    step   6 git_commit
    step   7 git_push
    step   8 checkout_branch
    step   9 git_pull
    step  10 run_submodule_update_recursive
    step  11 run_make_pull
    step  12 git_add_dash_u
    step  13 git_commit
    step  14 git_push
    step  15 bump_release
    step  16 check_version_updates
    step  17 add_and_commit_submodules
    step  18 git_add_dash_u
    step  19 git_commit
    step  20 merge_dot_x_branches_into_release_branches
    step  21 verify_merge
    step  22 run_make_clean
    step  23 run_make_install
    step  24 run_make_test
    step  25 commit_each_submodule
    step  26 git_add_dash_u
    step  27 git_commit
    step  28 publish_signed
    step  29 push_submodules
    step  30 git_push
    step  31 comment
```
- Run the publish script for real
  - if we need to restart for some reason, --start-step and --stop-step can be used to control execution

```
python publish/publish_new_release.py --repo $REPO --release 3.4 --bump-type minor
```

> If any of the steps fail then the script will exit immediately and it will tell you where to look to find the
> output of the failed step. In general the logging from each individual step will be in a 
>

### Close and Publish the release on Sonatype

This is an interactive GUI on the [oss.sonatype.org](https://oss.sonatype.org) website

#### [Instructions to finalize release on sonatype](sonatype_finalize_release.md)

## Finish up

```
python publish/tag_new_release.py
```

Or if you are the cautious type run it first with

```
python publish/tag_new_release.py --dry-run
```

Check the output then run it to do the tagging

```
python publish/tag_new_release.py
```


