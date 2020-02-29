'''
repocommits2db.repocommits2db -- extract commits from GitHib repo and store them in a local database

@author:     Jim Lawson

@copyright:  2020 UC Berkeley. All rights reserved.

@license:    BSD-3-Clause

@contact:    ucbjrl@berkeley.edu
@deffield    updated: Updated
'''

import os
import re
import signal
import sys
# In order to use the newer GitHub API calls, we need to extend the GitHub object and to do that,
#  we need to a bug and add features to the github3/models.py.
# Ensure the path to our version is ahead of the default site-package path.
sys.path.insert(0,'../citSupport')

import traceback
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from citSupport.monitorRepos import BaseRepo
from pymongo.mongo_client import MongoClient
from github3.search import CommitSearchResult
from github3.structs import SearchIterator
from github3 import GitHub, models, users, git
from github3.pulls import ShortPullRequest

__all__ = []
__version__ = 0.1
__date__ = '2020-02-21'
__updated__ = '2020-02-21'

DEBUG = 1
TESTRUN = 0
PROFILE = 0

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

doExit = False
continueOnError = False

homeDir = os.getcwd()

def sigterm(signum, frame):
    global doExit
    print('repocommits2db: signal %d' % (signum))
    if signum == signal.SIGTERM:
        doExit = True


class areaRE:
    def __init__(self, area, reString):
        self.area = area
        self.reString = reString
        self.re = re.compile(self.reString)

class WorkContext:
    def __init__(self, path, since, branch):
        self.path = path
        self.since = since
        self.branch = branch

class BareCommitSearchResult(models.GitHubCore):
    """A representation of a commit search result from the API.

    This object has the following attributes:

    .. attribute:: author

        A :class:`~github3.users.ShortUser` representing the user who
        authored the found commit.

    .. attribute:: comments_url

        The URL to retrieve the comments on the found commit from the API.

    .. attribute:: commit

        A :class:`~github3.git.ShortCommit` representing the found commit.

    .. attribute:: committer

        A :class:`~github3.users.ShortUser` representing the user who
        committed the found commit.

    .. attribute:: html_url

        The URL to view the found commit in a browser.

    .. attribute:: sha

        The SHA1 of the found commit.

    """

    def _update_attributes(self, data):
        self._api = data["url"]
        self.author = users.ShortUser(data["author"], self)
        self.comments_url = data["comments_url"]
        self.commit = git.ShortCommit(data["commit"], self)
        self.committer = users.ShortUser(data["committer"], self)
        self.html_url = data["html_url"]
        self.repository = None
        self.score = None
        self.sha = data["sha"]
        self.text_matches = None

    def _repr(self):
        return "<BareCommitSearchResult [{0}]>".format(self.sha[:7])


class PullCommitSearchResult(models.GitHubCore):
    """A representation of a commit search result from the API.

    This object has the following attributes:

    .. attribute:: author

        A :class:`~github3.users.ShortUser` representing the user who
        authored the found commit.

    .. attribute:: comments_url

        The URL to retrieve the comments on the found commit from the API.

    .. attribute:: commit

        A :class:`~github3.git.ShortCommit` representing the found commit.

    .. attribute:: committer

        A :class:`~github3.users.ShortUser` representing the user who
        committed the found commit.

    .. attribute:: html_url

        The URL to view the found commit in a browser.

    .. attribute:: number

        The pull request for this commit.

    """
    class_name = "_PullCommitSearchResult"

    def _update_attributes(self, pull):
        from github3.pulls import Base, Head
        from uritemplate import URITemplate
        from github3 import orgs

        self._api = pull["url"]
        self.comments_url = pull["comments_url"]
        self.commits_url = pull["commits_url"]
        self.html_url = pull["html_url"]
        self.id = pull["id"]
        self.number = pull["number"]
        self.state = pull["state"]
        self.title = pull["title"]

        self.assignee = pull["assignee"]
        if self.assignee is not None:
            self.assignee = users.ShortUser(self.assignee, self)
        self.assignees = [users.ShortUser(a, self) for a in pull["assignees"]]
        self.base = Base(pull["base"], self)
        self.body = pull["body"]
        self.closed_at = self._strptime(pull["closed_at"])
        self.comments_url = pull["comments_url"]
        self.commits_url = pull["commits_url"]
        self.created_at = self._strptime(pull["created_at"])
        self.diff_url = pull["diff_url"]
        self.head = Head(pull["head"], self)
        self.html_url = pull["html_url"]
        self.id = pull["id"]
        self.issue_url = pull["issue_url"]
        self.links = pull["_links"]
        self.merge_commit_sha = pull["merge_commit_sha"]
        self.merged_at = self._strptime(pull["merged_at"])
        self.number = pull["number"]
        self.patch_url = pull["patch_url"]
        requested_reviewers = pull.get("requested_reviewers", [])
        self.requested_reviewers = [
            users.ShortUser(r, self) for r in requested_reviewers
        ]
        requested_teams = pull.get("requested_teams", [])
        self.requested_teams = [
            orgs.ShortTeam(t, self) for t in requested_teams
        ]
        self.review_comment_urlt = URITemplate(pull["review_comment_url"])
        self.review_comments_url = pull["review_comments_url"]
        self.repository = None
        if self.base:
            self.repository = self.base.repository
        self.state = pull["state"]
        self.statuses_url = pull["statuses_url"]
        self.title = pull["title"]
        self.updated_at = self._strptime(pull["updated_at"])
        self.user = users.ShortUser(pull["user"], self)

    def _repr(self):
        return "<PullCommitSearchResult [{0}]>".format(self.number)


class GitHub_NewCommits(GitHub):
    def __init__(self, gh):
        # Monkey-patch the GitHubCore methods we need to fix.
        from github3.models import GitHubCore
        from citSupport.github3_patched import models as fixedModels
        GitHubCore.__init__ = fixedModels.GitHubCore.__init__
        GitHubCore.__getattr__ = fixedModels.GitHubCore.__getattr__
        GitHubCore._json = fixedModels.GitHubCore._json

        # # Replace some functions in github3.modules
        # gh3 = sys.modules['github3.models']
        # gh3.__init__ = fixedModels.__init__
        # sys.modules['github3.models'] = gh3
#        sys.modules['github3.models'] = __import__('citSupport.github3_patched.models')
        super(GitHub, self).__init__({}, gh.session)

    def repo_commits(
            self,
            owner,
            repo,
            sha=None,
            path=None,
            author=None,
            since=None,
            until=None,
            number=-1,
            etag=None,
    ):
        """Find commits via the Repo Commits API.

        The query can contain any combination of the following supported
        qualifiers:

        - ``sha`` SHA or branch to start listing commits from. Default: the repository’s default branch (usually master).
        - ``path`` Only commits containing this file path will be returned.
        - ``author`` GitHub login or email address by which to filter by commit author.
        - ``since`` Only commits after this date will be returned. This is a timestamp in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ.
        - ``until`` Only commits before this date will be returned. This is a timestamp in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ.

        For more information about these qualifiers, see: https://developer.github.com/v3/repos/commits/

        :param str query:
            (required), a valid query as described above, e.g.,
            ``css repo:octocat/Spoon-Knife``
        :param int number:
            (optional), number of commits to return.
            Default: -1, returns all available commits
        :param str etag:
            (optional), previous ETag header value
        :return:
            generator of commit search results
        :rtype:
            :class:`~github3.search.commits.CommitSearchResult`
        """
        params = {}
        if sha:
            params["sha"] = sha
        if path:
            params["path"] = path
        if author:
            params["author"] = author
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        headers = {"Accept": "application/vnd.github.groot-preview+json"}
        url = self._build_url("repos", owner, repo, "commits")
        return SearchIterator(
            number,
            url,
            BareCommitSearchResult,
            self,
            params,
            etag,
            headers,
        )


    def repo_commit_pullrequest(
            self,
            owner,
            repo,
            sha,
            number=-1
    ):
        """Find pull request for specified commit via the Repo Commits API.

        The query can contain any combination of the following supported
        qualifiers:

        - ``sha`` SHA or branch to start listing commits from. Default: the repository’s default branch (usually master).

        For more information about these qualifiers, see: https://developer.github.com/v3/repos/commits/

       :return:
            pull request for specified commit
        :rtype:
            :class:`~github3.search.commits.CommitSearchResult`
        """
        params = {}
        headers = {"Accept": "application/vnd.github.groot-preview+json"}
        url = self._build_url("repos", owner, repo, "commits", sha, "pulls")
        return SearchIterator(
            number,
            url,
            PullCommitSearchResult,
            self,
            params,
            None,
            headers,
        )

def doWork(wc, verbose):
    modName = __name__ + '.doWork'
    path = wc.path
    since = wc.since
    branch = wc.branch
    
    # Find the local git repo from the path
    repoObj = BaseRepo(path)
    if repoObj is None:
        exit(1)
    # Connect to the GitHub repository
    repoObj.connect()
    isRepoLocal = False
    repo = None
    if isRepoLocal:
        repo = repoObj.repo
    else:
        repo = repoObj.remoterepo

    # Connect to the database
    client = MongoClient()
    db = client['git-' + repo.name]
    commitDB = db['release_commits']
    pullDB = db['release_pulls']
    if not isRepoLocal:
        # Grab each commit and insert it into the database
        cgh = GitHub_NewCommits(repoObj.gh)
        commits = cgh.repo_commits(repo.owner, repo.name, sha=branch, since=since)
#        assert isinstance(commits, SearchIterator)
        for commit in commits:
#            assert isinstance(commit, CommitSearchResult)
            commitId = commit.sha
            pulls = cgh.repo_commit_pullrequest(repo.owner, repo.name, commitId)
            pullRequestIDs = []
            for pull in pulls:
                pullRequestIDs.append(pull.number)
                dbPull = pull.as_dict()
                pullId = pull.number
                try:
                    insertId = pullDB.insert_one(dbPull).inserted_id
                    print(' '.join([str(pullId), str(insertId)]))
                except AttributeError:
                    pass

            dbCommit = commit.as_dict().copy()
            dbCommit["pullRequests"] = pullRequestIDs
            if False:
                try:
                    insertId = commitDB.insert_one(dbCommit).inserted_id
                    print(' '.join([str(commitId), str(insertId)]))
                except AttributeError:
                    pass
    if False:
        for dbCommit in commitDB.find({}):
            commitId = dbCommit['sha']
            print('%s' % (commitId))
    if True:
        for dbPull in pullDB.find({}):
            commitId = dbPull['number']
            print('%s' % (commitId))


def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by Jim Lawson on %s.
  Copyright 2017 UC Berkeley. All rights reserved.

  Licensed under the BSD-3-Clause license
  https://opensource.org/licenses/BSD-3-Clause

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    global continueOnError
    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('-r', '--repo', dest='repo', help='repository to slurp', default='.', metavar='path')
        parser.add_argument('-s', '--since', dest='since', help='since (YYYY-MM-DD)', default=None)
        parser.add_argument('-b', '--branch', dest='branch', help='branch to search', default=None)

        # Process arguments
        args = parser.parse_args()

        verbose = args.verbose

        if verbose > 0:
            print("Verbose mode on")
        workContext = WorkContext(args.repo, args.since, args.branch)

        # Install the signal handler to catch SIGTERM
        signal.signal(signal.SIGTERM, sigterm)
        doWork(workContext, verbose)
        return 0
 
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        if not(DEBUG or TESTRUN):
            indent = len(program_name) * " "
            sys.stderr.write(program_name + ": " + repr(e) + "\n")
            sys.stderr.write(indent + "  for help use --help")
        return 2

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-v")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'repocommits2db.repocommits2db_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    main()
