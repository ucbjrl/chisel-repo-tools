'''
repopulls.repopulls -- extract pull requests from GitHib repo

repopulls.repopulls is a module that connects to a GitHub repo and extracts pull request information.

@author:     Jim Lawson

@copyright:  2017 UC Berkeley. All rights reserved.

@license:    license

@contact:    ucbjrl@berkeley.edu
@deffield    updated: Updated
'''

import os
import re
import signal
import sys
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from citSupport.monitorRepos import MonitorRepos

__all__ = []
__version__ = 0.1
__date__ = '2017-10-17'
__updated__ = '2017-10-17'

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

localRepoNames = [ '/Users/jrl/noArc/clients/ucb/git/ucb-bar/chisel3:release']
unweightedLogins = set(['Lawson_Jim'])
doExit = False
continueOnError = False

homeDir = os.getcwd()

def sigterm(signum, frame):
    global doExit
    print 'repopulls: signal %d' % (signum)
    if signum == signal.SIGTERM:
        doExit = True


class areaRE:
    def __init__(self, area, reString):
        self.area = area
        self.reString = reString
        self.re = re.compile(self.reString)

def doWork(paths, verbose):
    modName = __name__ + '.doWork'
    
    repos = MonitorRepos(paths)
    if repos is None:
        exit(1)
    
    for (repoName, repoObj) in repos.repoMap.iteritems():
        isRepoLocal = False
        repo = None
        if isRepoLocal:
            repo = repoObj.repo
        else:
            repo = repoObj.remoterepo

        if not isRepoLocal:
            sha = ''
            for pr in repo.pull_requests(state='closed', number=1):
                title = pr.title if pr.title and pr.title != '' else pr.body_text
                body = pr.body_text
                files = [f.filename for f in pr.files()]
                id = str(pr.id)
                number = str(pr.number)
                print ' '.join([id, number, title, body])
#        for commit in repo.remoterepo.iter_commits():
#        for commit in repo.iter_commits() if isRepoLocal else repo.commits():
#             try:
#                 if isRepoLocal:
#                     sha = commit.hexsha
#                 else:
#                     commit.refresh()
#                     sha = commit.sha
# 
#             except Exception, e:
#                 print '%s in %s' % (e, modName)
#                 raise(e)


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

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

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
        parser.add_argument(dest="paths", help="paths to folders containing clones of github repositories to be tested [default: %(default)s]",  default=localRepoNames, metavar="path", nargs='*')

        # Process arguments
        args = parser.parse_args()

        paths = args.paths
        verbose = args.verbose

        if verbose > 0:
            print("Verbose mode on")

        # Install the signal handler to catch SIGTERM
        signal.signal(signal.SIGTERM, sigterm)
        doWork(paths, verbose)
        return 0
 
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception, e:
        if DEBUG or TESTRUN:
            raise(e)
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
        profile_filename = 'repopulls.repopulls_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    main()
