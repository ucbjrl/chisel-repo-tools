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
