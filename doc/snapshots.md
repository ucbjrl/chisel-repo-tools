

# Snapshot (from master) Preparation Details (07/27/20)

This assumes that changes in master need to be manually merged with the Z.Y.x current release branch. 

## 1. Set up environment
source ~/.virtualenvs/cit3/bin/activate

## 2. Create a release repository
```
clone chisel-release repository
git clone https://github.com/ucb-bar/chisel-release.git release-snapshots
cd release-snapshots
```
## 3. Update master branch
### 3.1 Checkout master branch and pull in changes from origin
```
git checkout master
git pull
```
### 3.2 Populate submodules
```
git submodule update --init --recursive
```

### 3.3 Position submodules at head of master branches
```
make pull
```

### 3.4 Update top level
```
git add -u
```

### 3.5 Commit
git commit -m "Bump versions"

### 3.6 Push
```
git push
```
---
### 4. Update .x branch
#### 4.1 Checkout .x branch
```
git checkout <<major>>.<<sub-major>>.x
git pull
```
### 4.2 Populate submodules
```
git submodule update --init --recursive
```
### 4.3 Position submodules at head of .x branch
```
make pull
```
### 4.4 Update top level
```
git add -u
```
### 4.5 Commit
```
git commit -m "Bump versions"
```
---
## 5. Merge master branches into .x branches
### 5.1 Merge individual .x branches with their respective master
```
git submodule foreach '
  if git diff --cached --quiet; then git merge --no-ff --no-commit master;
  fi
'
```
### 5.2 Verify
```
git status -b -uno --ignore-submodules=untracked
python $VERSIONING verify
```
---
## 6. Test merged configuration
### 6.1 Verify verilator
```
verilator -version
```
### 6.2 Verify yosys
```
yosys -V
```
### 6.3 Verify z3
```
z3 --version
```
### 6.4 Run tests
```
make -j 8 clean install test >& make-clean-install-test.out
check test results
```

### 6.5 See if any failures happened, if so debug away
```
grep 'ests: succeeded' make-clean-install-test.out
tail -100 make-clean-install-test.out
grep '\[error\]' make-clean-install-test.out
```
---
### 7. commit merges
### 7.1 Commit each submodule
```
git submodule foreach 'if git diff --cached --quiet ; then echo skipping ;  else git commit --no-edit ; fi'
```

### 7.2 Push the submodules
```
git submodule foreach 'git push'
```

### 7.3 Add updated submodules
```
git add -u
```

### 7.4 Commit top level
```
git commit -m "Release Z.Y.X prep"
```

### 7.5 Push top level
```
git push
```




