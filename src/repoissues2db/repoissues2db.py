'''
repoissues2db.repoissues2db -- extract issues and commits from GitHib repo and store them in a local database

@author:     Jim Lawson

@copyright:  2019 UC Berkeley. All rights reserved.

@license:    BSD-3-Clause

@contact:    ucbjrl@berkeley.edu
@deffield    updated: Updated
'''

import os
import re
import signal
import sys
import traceback
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from citSupport.monitorRepos import BaseRepo
from pymongo import MongoClient
from github3.github import GitHub
from github3.search import IssueSearchResult
from github3.structs import SearchIterator
from docutils.parsers.rst.directives import path

__all__ = []
__version__ = 0.1
__date__ = '2019-09-26'
__updated__ = '2019-09-26'

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
    print 'repoissues2db: signal %d' % (signum)
    if signum == signal.SIGTERM:
        doExit = True


class areaRE:
    def __init__(self, area, reString):
        self.area = area
        self.reString = reString
        self.re = re.compile(self.reString)

class WorkContext:
    def __init__(self, path, since):
        self.path = path
        self.since = since

def doWork(wc, verbose):
    modName = __name__ + '.doWork'
    path = wc.path
    since = wc.since
    
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
    db = client['git' + repo.name]
    issueDB = db['issues']
    eventDB = db['issue_events']
    commitDB = db['pr_commits']
    if not isRepoLocal:
        # Build the query for GitHub - keep it pretty simple
        query = 'repo:' + repo.full_name
        if since:
            query += ' closed:>' + since
        # Grab each issue and insert it into the database
        issues = repoObj.gh.search_issues(query)
        assert isinstance(issues, SearchIterator)
        for issue in issues:
            assert isinstance(issue, IssueSearchResult)
            issueId = issue.issue.id
            try:
                insertId = issueDB.insert_one(issue.as_dict()).inserted_id
                print ' '.join([str(issueId), str(insertId)])
            except AttributeError:
                pass
    if True:
        for dbIssue in issueDB.find({}):
            issueId = dbIssue['number']
            print '%d' % (issueId)
            repoIssue = repo.issue(issueId)
            isPR = hasattr(repoIssue, 'pull_request_urls') and repoIssue.pull_request_urls is not None and len(repoIssue.pull_request_urls) > 0
            if False:
                for event in repoIssue.events():
                    event['issue'] = issueId
                    eventId = event.id
                    try:
                        insertId = eventDB.insert_one(event.as_dict()).inserted_id._inc
                        print ' '.join([str(eventId), str(insertId._pid)])
                    except AttributeError:
                        pass
            if True and isPR:
                # If the issue is a pull request, grab its associated commits and insert them in the database
                try:
                    repoPR = repo.pull_request(issueId)
                    for shortCommit in repoPR.commits():
                        commit = shortCommit.as_dict()
                        commit['pr'] = issueId
                        commitId = commit['sha']
                        try:
                            insertId = commitDB.insert_one(commit).inserted_id._inc
                            print ' '.join([commitId, str(insertId)])
                        except AttributeError:
                            pass
                except:
                    print 'Bang!'
                


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

        # Process arguments
        args = parser.parse_args()

        verbose = args.verbose

        if verbose > 0:
            print("Verbose mode on")
        workContext = WorkContext(args.repo, args.since)

        # Install the signal handler to catch SIGTERM
        signal.signal(signal.SIGTERM, sigterm)
        doWork(workContext, verbose)
        return 0
 
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception, e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
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
        profile_filename = 'repoissues2db.repoissues2db_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    main()
