# Python Virtual Environment Setup

## Here is the current recipe for setting this up

```
python -m venv ~/.virtualenvs/repo-tools-python
source ~/.virtualenvs/repo-tools-python/bin/activate
/Users/chick/.virtualenvs/repo-tools-python/bin/python -m pip install --upgrade pip
```
This next step should not be necessary but currently is, will not process all requirements correctly without it
```
pip install pygithub
```
```
pip install -r resources/requirements.txt
python src/release_scripts/build_masters.py -r ../pub-snap/ --stop-step 4
```

## Activating Python Virtual Environment
To activate at any later time just do
```
source ~/.virtualenvs/repo-tools-python/bin/activate
```

## IMPORTANT environment variables.
These two variables are necessary to run most of the scripts mentioned in this project. To set them
it is easiest to `cd` into the chisel-repo-tools directory
and run the following steps at the bash command line
```
export PYTHONPATH=`pwd`/src
export VERSIONING=`pwd`/src/versioning/versioning.py
```
>Note: the more generic way to set PYTHONPATH is ```export PYTHONPATH=`pwd`/src:$PYTHONPATH``` which will
>retain any other python path info you may have

## Virtual env location.
TODO: Figure out the best place to put this environment, particularly with respect to it's use
as a `cron`ed job for regular publishing of snapshots. It would be good to cache this somehow
to minimize setup overhead. It might be best to just install inside the repo and have .gitignore
to prevent it from being committed to github.

## Requirements
The requirement file `resources/requirements.txt` may need to be regenerated from time to time
as libraries change or new ones comem into play. The file can be regenerated via
```
pip freeze > resources/requirements.txt
```
It would be fine to put this into some other file to test first.
