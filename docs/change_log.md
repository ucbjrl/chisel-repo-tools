# ChangeLog Details (06/25/20)
>For running on mac use  `brew tap mongodb/brew`

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






