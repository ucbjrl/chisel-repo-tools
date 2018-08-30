#!/usr/local/bin/python2.7
# encoding: utf-8
'''
addlabels.addlabels -- add labels to GitHub pull request

addlabels.addlabels is a scheduled task to read GitHub pull requests and determine labels based on the pull request text, assuming the PR conforms to the standard template.

It defines classes_and_methods

@author:     Jim Lawson

@copyright:  2017 UC Berkeley. All rights reserved.

@license:    BSD

@contact:    ucbjrl@berkeley.edu
@deffield    updated: Updated
'''

import sys
import os

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from citJenkins.monitorRepos import BaseRepo
from bs4 import BeautifulSoup

__all__ = []
__version__ = 0.1
__date__ = '2017-12-08'
__updated__ = '2017-12-08'

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

class ChiselLabels:
    labels = {'Type of change' : {'Bug report': 'bug', 'Feature request': 'feature request', 'Other enhancement': 'other enhancement'},
              'Impact' : {'no functional change': 'no functional change', 'API addition (no impact on existing code': 'API Addition', 'API modification': 'API Modification'},
              'Development Phase' : {'proposal': 'proposal', 'implementation': 'implementation'}
              }
    @staticmethod
    def label(category, selector):
        return ChiselLabels.labels[category][selector]
        
def addLabel(repoPath, pullRequestNumber):
    modName = __name__ + '.addLabel'
    
    baseRepo = BaseRepo(repoPath)
    if baseRepo is None:
        exit(1)
    baseRepo.connect()
    repo = baseRepo.remoterepo
    
    sha = ''
    issue = repo.issue(number=pullRequestNumber)
    body = issue.body_text if issue.body_text else ''
    title = issue.title if issue.title and issue.title != '' else body
    soup = BeautifulSoup(issue.body_html, 'html.parser')
        
    print str(pullRequestNumber) + ': ' +  ', '.join([x.name for x in issue.labels()])
    print issue.body_html
    for checkbox in soup.find_all('input', checked=True):
        category = checkbox.find_previous('p').text.strip()
        selector = checkbox.text.strip()
        print ChiselLabels.label(category, selector)

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

  Licensed under the BSD License

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('-r', '--repo', dest='repo', help="repository", type=str)
        parser.add_argument('-p', '--pullRequest', dest='pullRequest', help="pull request", type=int)

        # Process arguments
        args = parser.parse_args()

        repo = args.repo
        pullRequest = args.pullRequest
        verbose = args.verbose

        if verbose > 0:
            print("Verbose mode on")

        addLabel(repo, pullRequest)
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
        profile_filename = 'addlabels.addlabels_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())