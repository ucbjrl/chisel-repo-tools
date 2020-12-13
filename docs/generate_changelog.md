# Generating a Changelog

This document describes creating release notes for a **Chisel** release. At present this is a crude process that looks
through the github repos `PR`s that were closed between the times of the publications of the previous release and the
current one. It then parses them for text describing the changes of each `PR`. Some of the chisel repos have reserved
sections of the `PR` for the committer to describe the changes. The output of the script described here is a single text
file `changelog.txt` file with all the text organized by repo. This file will then require some editing to generate the
final **Release Notes** for each repo.

## Overview

This function involves using the github api to pull references of issues from github and put those references in a
local `mongo` database. After that initial step those refernces are run through and more detailed selection takes place
(validing issue is a `PR`, etc) and the database is populated with additional information during this phase.
> Note: It is possible during this phase that API throughput limits may be hit.
> Carefully choosing the smallest possible date range can reduce the number of issues that need to be examined.

> Note: If re-running this script it is possible that there will be old issues that are not in the range.
> While this does not affect the output it can affect the API throughput mentioned above. Use the
> `--clear-db` flag to clear database before download If you have gotten this far you should be familiar with how set up an enviroment for running this script. See [Publishing Setup](publishing_setup.md) and [Python Setup](python_venv_setup.md)

Later steps will run through the local database and extract the short descriptions of the changes and ultimately
organize them into a `change_log.txt` file. This file currently requires a fair amount of human massaging before adding
the final text to the release notes for each repository for the release in question.

## The script you will be using is

```
python src/release_scripts/generate_changelog.py
```

Like other scripts from this directory it runs a series of commands.

## Running the script

``` 
python src/release_scripts/generate_changelog.py --help
usage: generate_changelog.py [-h] -r RELEASE_DIR -m MAJOR_VERSION [-d DATE_RANGE] [-c]
                             [-g GITHUB_TOKEN] [-b START_STEP] [-e STOP_STEP] [-l]

optional arguments:
  -h, --help            show this help message and exit
  -r RELEASE_DIR, --release RELEASE_DIR
                        a directory which is a clone of chisel-release
  -m MAJOR_VERSION, --major-version MAJOR_VERSION
                        major number of snapshots being published
  -d DATE_RANGE, --date-range DATE_RANGE
                        set dates to search for PRs, e.g. ">2021-04-01" or "2021-05-01..2021-05-31
  -c, --clear-db        clears issues collection from each repo database before downloading
  -g GITHUB_TOKEN, --github-token GITHUB_TOKEN
                        Way to set your github token, will use env var GHRPAT if not set by this
  -b START_STEP, --start-step START_STEP
                        command step to start on
  -e STOP_STEP, --stop-step STOP_STEP
                        command step to end on
  -l, --list-only       list command step, do not execute
```

with steps

``` 
python src/release_scripts/generate_changelog.py --release $REPO -m 3.4 --list-only
chisel-release directory is /Users/chick/Adept/dev/release-generators/chisel-repo-tools
release specified is 3.4.x
These are the steps to be executed for the src/release_scripts/generate_changelog.py script
step   1 checkout_branch
step   2 git_pull
step   3 run_submodule_update_recursive
step   4 run_submodule_fetch_from_origin
step   5 populate_db_with_request_issues
step   6 verify_version_tag
step   7 generate_git_log_one_liners
step   8 generate_changelog
```

To run.

``` 
python src/release_scripts/generate_changelog.py --release $REPO --major-version 3.4 --date-range "2021-05-01..2021-05-31" --clear-db
```

---
---

## Original documentation

This is a copy of the original documentation for this proces. these steps have been integrated into
the `generated_changelog.py` script.

## ChangeLog Details (06/25/20)

> For running on mac use  `brew tap mongodb/brew`

### Checkout version

```
git checkout Z.Y-release
git pull
git submodule update --init --recursive
git submodule foreach 'git fetch origin'
```

### populate database with pull requests/issues
```
export GHRPAT=XXX
```
where XXX is your GITHUB token
```
git submodule foreach '
  cd .. &&
  python $PYTHONPATH/repoissues2db/repoissues2db.py -r $name -s 2020-04-01
'
```
### Verify version tag selection is accurate
```
git submodule foreach '
  branch=$(sh ../major-version-from-branch.sh) &&
  tags=($(git tag -l --sort=v:refname |
  grep -v SNAPSHOT |
  tail -n 2));
  echo ${tags[0]} .. ${tags[1]}
 '
```
### Generate git log one-liners
```
git submodule foreach '
  branch=$(sh ../major-version-from-branch.sh) &&
  tags=($(git tag -l --sort=v:refname |
  grep -v SNAPSHOT |
  tail -n 2));
  echo ${tags[1]};
  git log --oneline ${tags[0]}..${tags[1]} > releaseNotes.${tags[1]}
'
```
### Generate changelog
```
git submodule foreach '
  branch=$(sh ../major-version-from-branch.sh) &&
  tags=($(git tag -l --sort=v:refname |
  grep -v SNAPSHOT | tail -n 2));
  echo ${tags[1]};
  python $PYTHONPATH/gitlog2releasenotes/gitlog2releasenotes.py -b git-$name releaseNotes.${tags[1]}
‘ > changelog.txt
```
### Edit changelog
- Manually edit the changelog.txt file 
- Goal is one line per PR

### Update github
- Select repo
- Releases
- Draft new release
- Add version number
- Add description, either 
- list of PR’s or ‘Bump dependencies’

### Example
- go to https://github.com/freechipsproject/firrtl
- click on release
- click on draft new release 
- paste in text
- set tag to 1.4.0
- save it.

### Edit data from changelog.txt from step 6 above.
- Fiddle with it
- Save draft -- gives chance for others to review
- click `This is pre-release`






