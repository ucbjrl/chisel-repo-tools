# repo-tools is a Python Module providing various git/sbt support methods.

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
