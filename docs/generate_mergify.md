# Generating a Mergify file

[Mergify](https://mergify.io/) is tool that automates backporting and other release management. It is used by creating
a `.mergify.yml` configuration file. This document describes, briefly, `merigfy.sc` a script that constructs
a `.merigify.yml` file.
`merfigy.sc` requires a parameters/template file in order to operate.

The [chisel-repo-tools](https://github.com/ucb-bar/chisel-repo-tools) contains a sample parameters file
in `resources/mergify.sc.example.params`

## Requirements

- This script uses [mill](https://github.com/lihaoyi/mill). Check there for installation instructions.
- It also requires [Ammonite](https://ammonite.io/) for running mill scripts

## Parameters file.

Here is an example parameters file

```
conditions:
  - status-success=Travis CI - Pull Request
branches:
  - 1.2.x
  - 1.3.x
  - 1.4.x
```

> Note: `status-success` field should match the task name of the continuous integration process used in your repo

> Note: The order of the backporting tree should be low versions to high.

## Running

- Clone the chisel-repo-tools and point to it

```
git clone https://github.com/ucb-bar/chisel-repo-tools <dir>
export REPOTOOLS=<dir>
```

- Get in a git repository where you want to create a `.mergify.yml` file
- Get a local copy of the parameters file

```
cp $REPOTOOLS/resources/mergify.sc.example.params myparams
```

- Edit the local copy `myparams`
  - Set the status-success to refer to your local ci task name
  - List the .x versions going low to high of the versions you want automatic backports to be generated for
- Run the command

```
$REPOTOOLS/scripts/mergify.sc --template myparams > .mergify.yml
```

- Incorporate with your repo
  - follow your practices for incorporating new code (branches, commit, review etc)

