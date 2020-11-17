# Release Process Details (06/25/20)
This is the original documentation for running a release process. This document is realized in the 
script `src/release_scripts/publish_new_release.py`. Some aspect of the process may vary from this
original document but this is a good reference for the steps that have to happen.
In this document Z.Y refers to the current (two-part) major number of the chisel eco-system. This number
is not currently shared by all submodules of this. The scripts are aware of this and manage it.

## Preparation
User has cloned chisel-repo-tools and chisel-release in a common directory

```
mkdir workdir
cd workdir
git clone https://github.com/ucb-bar/chisel-release.git
clone chisel-repo-tools repository
git clone https://github.com/ucb-bar/chisel-repo-tools.git
```

## Set up the python environment
See: [Python Virtual Environment Setup](python_venv_setup.md)

## Update the .x branch of chisel-release
### Checkout the .x branch
```
git checkout Z.Y.x
git pull
```

### Populate Submodules
```
git submodule update --init --recursive
```

### Position Submodules at head of .x branches
```
mkdir stamps
make pull
```

### Update Top Level
```
git add -u
git commit -m "Bump versions"
git push
```

### Update the Z.Y-release Branch
```
git checkout Z.Y-release
git pull
```
### Populate Submodules
```
git submodule update --init --recursive
```
### Position Submodules at Head of Branch
```
make pull
```
### Update Top Level
```
git add -u
git commit -m "Bump versions"
git push
```

## Bump Z.Y-release Branch Versions
Use $VERSIONING script to bump versions (USE ONLY ONE OF THESE) to create
### date-stamped SNAPSHOT
```
python $VERSIONING -s "20200630" write
python $VERSIONING -s "" write
```
### Bump Major Version
```
python $VERSIONING bump-max
```
### Prepare Major Release Candidate
```
python $VERSIONING -r "RC<<candidate-number>>" write
```
### New Release After Candidates
```
python $VERSIONING -r "" write
```
### Bump Minor Version
```
python $VERSIONING bump-min
```
### Verify Version Bumps
```
git diff --submodule=diff
```
>IMPORTANT: Not automated
>The only differences should be the version.yml file and the versions in the submodule build.sbt and build.sc files.

### Commit Version Bumps
```
git submodule foreach 'git add -u && git commit -m "Bump version strings." '
```

### Add Updated Branches and Update version.yml
commit updated branches and update version.yml
```
git add -u
git commit -m "Bump version strings."
```
### Merge .x Branches into -release Branches
Run merge script, you may need to loop on this step while fixing any conflicts in the submodules (this will typically be in the build.* files)
./merge-release-with-x.sh
>IMPORTANT: Check of this step is not automated, you must look at the output.
### Verify
git status -b -uno --ignore-submodules=untracked
>IMPORTANT: Check of this step is not automated, you must look at the output.

## Test Release Configuration
### Verify necessary external programs are available
```
verilator -version && yosys -V && z3 --version && echo "All programs found"
```
>IMPORTANT: If you don't see "All programs found" in the output you are missing something.

### Run Tests
Run tests and eyeball the output to see if anything failed.
```
make -j 8 clean install test >& make-clean-install-test.out
grep '\[error\]' make-clean-install-test.out
```

## Commit Merges
### commit each submodule
```
git submodule foreach '
if git diff --cached --quiet ; then echo skipping ; else
git commit --no-edit
fi
'
```

### Add Updated Submodules
```
git add -u
```
### Commit Top Level
```
git commit -m "Release Z.Y.X"
```
## Push Release
### Push Submodules
```
git submodule foreach '
  git push
'
```
### Push top level
```
git push
```
## Publish Release
### publish signed
Publishes the release to sonatype for all supported scala versions
```
make +publishSigned
```

## Finalize the Release on Sonatype

Follow instructions in [Sonatype Finalize Release](sonatype_finalize_release.md)

### Tag Submodule Release Branches
```
 git submodule foreach '
 rbranch=$(git config -f $toplevel/.gitmodules submodule.$name.branch);
 xbranch=$(echo $rbranch | sed -e "s/-release/.x/");
 eval git tag $(../genTag.sh $xbranch)
'
```
>After running above (assuming all looks good) change the echo to an eval and re-run.

```
git submodule foreach 'git describe'
git submodule foreach 'git push origin $(git describe)'
```
### Tag Top Level Branch
```
eval git tag $(./genTag.sh Z.Y.x vZ.Y.X)
git describe
git push origin $(git describe)
```
### Publish SNAPSHOT Version
In general, whenever a fixed release is published (either date-stamped SNAPSHOT or major or minor release,
a corresponding non-date-stamped SNAPSHOT should also be published.
To do this, temporarily change the published version for each submodule (but not its dependencies).
This ensures that builds using the SNAPSHOT will be reproducible, at least until the next SNAPSHOT is published.
### Checkout -release Branch
```
git checkout Z.Y-release
git pull
git submodule update --init --recursive
```
### Temporarily set root versions for each submodule
```
python $VERSIONING -s "" --onlyroot write
```
### Verify the (temporary) changes
git diff --submodule=diff
### Clean and install
```
make -j 8 clean install
```
### PublishSigned
```
make +publishSigned
```
### Undo version changes
```
git checkout version.yml
```
Then run
```
python $VERSIONING write
```
     or
```
git checkout version.yml
git submodule foreach 'git checkout $(git ls-files --modified)'
```
## Generate change log
### publish version changelogs to GitHub
