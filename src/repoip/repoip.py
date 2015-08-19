#!/usr/local/bin/python2.7
# encoding: utf-8
'''
repoip.repoip -- pull info from github repo

repoip.repoip is a package for converting repo info (issues and pull requests) to CSV format

It defines basic html to CSV conversion routines

@author:     Jim Lawson

@copyright:  2015 UC Berkeley Regents. All rights reserved.

@license:    Apache

@contact:    ucbjrl@berkeley.edu
@deffield    updated: Updated
'''
from __future__ import print_function

import csv
import os
import signal
import string
import sys

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from citJenkins.monitorRepos import MonitorRepos

__all__ = []
__version__ = 0.1
__date__ = '2015-08-18'
__updated__ = '2015-08-18'

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

localRepoNames = [ '/Users/jrl/noArc/clients/ucb/git/ucb-bar/chisel:master']

doExit = False
continueOnError = False
pullFields = [
              'number',
              'title',
              'user_full_name',
              'created_at',
              'modified_at',
              'updated_at',
              'body',
              'diff_url'
              ]

issueFields = [
              'number',
              'user_login',
              'labels',
              'title',
              'created_at',
              'updated_at',
              'assignee_login',
              'pull_request',
              'body'
              ]

def sigterm(signum, frame):
    global doExit
    print ('repoip: signal %d' % (signum))
    if signum == signal.SIGTERM:
        doExit = True

# Generate a translation table for delimiters - converting tabs or newlines into spaces.
delimTranslate = string.maketrans('\t\n\r', '   ')
def utf_8_encoded(d):
    result = d
    for k in result.keys():
        item = result[k]
        if isinstance(item, unicode):
            result[k] = item.encode('utf-8').translate(delimTranslate)
        elif isinstance(item, str):
            result[k] = item.translate(delimTranslate)
    return result

def doWork(paths, verbose, outputDir):
#    modName = __name__ + '.doWork'
    
    repos = MonitorRepos(paths)
    if repos is None:
        exit(1)
    
    osep = '\t'
    # Generate a translation table for converting a repo:branch into a legal file name
    fileNameTranslate = string.maketrans(':/', '__')
    for (repoId, repoObj) in repos.repoMap.iteritems():
        repo = repoObj.remoterepo
        ownerName, repoName = repo.full_name.encode('utf-8').split('/')
        csvFileName = repo.full_name.encode('utf-8').translate(fileNameTranslate) + '_' + repoObj.branch

        with open(os.path.join(outputDir, csvFileName + '.issues.csv'), 'wb') as outputFile:
            csvOut = None
            for issue in repo.issues(state='open'):
                issue.refresh()
                issuedict = issue.as_dict()
                if csvOut is None:
                    csvOut = csv.DictWriter(outputFile, issueFields, dialect='excel-tab', delimiter=osep, extrasaction='ignore')
                    csvOut.writeheader()

                issuedict['assignee_login'] = issue.assignee.login if issue.assignee else None
                issuedict['user_login'] = issue.user.login
                labels = []
                for label in issue.labels():
                    labelText = label.as_dict()[u'name']
                    labels.append(labelText)
                issuedict['labels'] = ', '.join(labels)
                csvOut.writerow(utf_8_encoded(issuedict))

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
  Copyright 2015 UC Berkeley Regents. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('-o', '--outputDir', dest='outputDir', metavar="path", default='.')
        parser.add_argument(dest="paths", help="paths to folder(s) with source file(s) [default: %(default)s]", metavar="path", nargs='+')

        # Process arguments
        args = parser.parse_args()

        paths = args.paths
        verbose = args.verbose
        outputDir = args.outputDir

        if verbose > 0:
            print("Verbose mode on")

        # Install the signal handler to catch SIGTERM
        signal.signal(signal.SIGTERM, sigterm)
        doWork(paths, verbose, outputDir)
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
        profile_filename = 'repoip.repoip_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())