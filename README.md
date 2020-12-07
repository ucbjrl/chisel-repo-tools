# Chisel Repo Tools
**chisel-repo-tools** is a set of tools used for creating and updating chisel releases.
It is designed to be used in conjuction with the [chisel-release](https://github.com/ucb-bar/chisel-release) repository.

## Release processes
There are several parts here
### Release python scripts
The python scripts the various release processes are in the src/release_scripts directory
Currently there the following scripts

| script | what it does |
| --- | --- |
| build_masters | updates the chisel-release master with master versions of all BigN chisel repos and runs tests.|

- scripts should respond to `--help` with mor information
- scripts should have `--start-step <n>` to skip over tests while starting
- scripts should have `--stop-step <n>` to stop after a particular step

### How to use

#### Other requirements
Scripts that run tests on the BigN repos require a few external programs to be in the executable path.

| program | version |  what it does |
| --- | --- | --- |
| verilator | \>= 4.016 | builds c++ circuit simulators |
| yosys | \>= 0.9 | used for in firrtl equivalence tests |
| z3 | \>= 4.8.9 | used to test SMT backend |
 
#### Create a directory for your work
#### Setup python
We recommend using a python3 virtual enviroment.
```
source ~/.venvs/chisel-release-python/bin/activate
```
See: [Appendix Setting up python virtual environment]
#### get tools
```
git clone https://github.com/ucb-bar/chisel-repo-tools
```
#### Get a release copy
```
git clone https://github.com/ucb-bar/chisel-release my-release-dir
```
#### Run your script
```
cd chisel-repo-tools
export PYTHONPATH=`pwd`/src
python src/release_scripts/<desired-script> --repo ../chisel-release 
```

## Python Modules
is a Python Module providing various git/sbt support methods.

- addlabels (WIP) - analyze/add labels to GitHub repo
- citSupport is a Python Module providing support for managing continuous integration builds. It contains two main sub-modules:
   - MonitoreRepos - monitor one (or more) GitHub repo for push events,
   - testRun - execute a sequence of shell commands to build and test.
  **NOTE** citSupport current contains a patched version of github3.models to work around bugs/deficiencies.
- cltext2html: - htmlify a changelist text file.
- countlabels (WIP) - count label usage
- cwr: compare with replace - compare two text files, allowing for token/word replacements.
- getlabels - download labels from GitHub
- github-traffic-api: - use the traffic api to get the past two weeks of github cloning traffic.
- githubTrafficScraper (abandoned) - variant of github-traffic-api
- gitlog2releasenotes - generate ReleaseNotes/ChangeLog from `git log --oneline` and GitHub downloaded issues in mongo db
- json2shellvar (abandoned) - convert json array to bash shell array variable (GitHub action/workflow tooling)
- mongodbtext (abandoned) - python/mongodb interface testing
- printenv (abandoned) - python access to environment
- repocommits2db (abandoned) - github2 API experimentation
- repocontributors - print repo contributor information from git/GitHub 
- repoip (abandoned) convert repo info (issues and pull requests) to CSV format
- repoissues2db - download issues/pull requests into momgodb
- repopulls (abandoned) - github3 API experimentation
- repopulls2db (abandoned) - github3/mongodb experimentation
- sbttest: generate CSV file from sbt test output
- sortnames: test
- tableify: htmlify / delimited table entries
- timetrials: extract timing information from a build run.
- updatelabels (WIP) - reconcile labels between repositories
- version - basic version object
- versioning - manage version numbers and dependencies for a collection of repositories

In order to access what may be protected repository information, this application needs to be able to authenticate
itself to GitHub, and in order to do so, it uses a personal API token, which it assumes is contained in the
environment variable GHRPAT.

see:
- https://developer.github.com/guides/basics-of-authentication
- https://developer.github.com/v3/auth/#basic-authentication
- https://developer.github.com/v3/oauth_authorizations/
- https://developer.github.com/v3/oauth/
- https://github.com/blog/1509-personal-api-tokens

## Appendix Setting up python virtual environment
python -m ~/.venv chisel-release-python

