'''
mongodbtext.mongodbtext -- extract text from a mongo database containing github repo data

mongodbtext.mongodbtext is a module that connects to a mongo database and extracts various text fields.

@author:     Jim Lawson

@copyright:  2017 UC Berkeley. All rights reserved.

@license:    license

@contact:    ucbjrl@berkeley.edu
@deffield    updated: Updated
'''
from __future__ import print_function

import os
import re
import signal
import sys
from string import maketrans
from argparse import ArgumentParser, FileType
from argparse import RawDescriptionHelpFormatter
from pymongo import MongoClient
import pymongo

__all__ = []
__version__ = 0.1
__date__ = '2017-11-02'
__updated__ = '2017-11-02'

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
    print ('mongodbtext: signal %d' % (signum), file=sys.stderr)
    if signum == signal.SIGTERM:
        doExit = True


class areaRE:
    def __init__(self, area, reString):
        self.area = area
        self.reString = reString
        self.re = re.compile(self.reString)

del_chars = " ".join(chr(i) for i in range(32) + range(127,256))
trans = maketrans(del_chars, " "*len(del_chars))
def onlyPrintable(s):
#    s.apply(lambda c: c.translate(trans))
#    s.replace({r'[^\x00-\x7F]+':''}, regex=True)
    return s.encode('ascii', 'ignore')

def doWork(outputFile=sys.stdout, filterFile=None, verbose=0):
    modName = __name__ + '.doWork'
    
    # Connect to the database
    client = MongoClient()
    db = client['github']
    pullRequestDB = db['pullRequests']
    pullCommitDB = db['pullCommits']
    pullCommitCommentDB = db['pullCommitComments']
    pullReviewCommentDB = db['pullReviewComments']
    issueDB = db['issues']
    issueCommentDB = db['issueComments']
    commitDB = db['commits']
    commitCommentDB = db['commitComments']
    reviewDB = db['reviews']
    prsToProcess = frozenset([int(x) for x in filterFile.readlines()] if filterFile else [])
    # Extract pull request comments
    for pr in pullRequestDB.find(sort=[('number', pymongo.ASCENDING)]):
        number = pr['number']
        author = onlyPrintable(pr['user']['login'])
        title = onlyPrintable(pr['title'] if pr['title'] else '')
        body = onlyPrintable(pr['body_text'] if pr['body_text'] else '')
        if len(prsToProcess) == 0 or number in prsToProcess:
            print ('#%s, %s - %s' % (number, author, title), file=outputFile)
            print (body, file=outputFile)


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
        parser.add_argument('-f', '--filterFile', dest='filterFile', type=FileType('r'), help='file containing pr numbers of interest')
        parser.add_argument(dest="outputFile", help="file where output should be written [default: %(default)]",  default=sys.stdout, type=FileType('w'), nargs='?')

        # Process arguments
        args = parser.parse_args()

        outputFile = args.outputFile
        filterFile = args.filterFile
        verbose = args.verbose

        if verbose > 0:
            print("Verbose mode on", file=sys.stderr)

        # Install the signal handler to catch SIGTERM
        signal.signal(signal.SIGTERM, sigterm)
        doWork(outputFile, filterFile, verbose)
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
        profile_filename = 'mongodbtext.repopulls2db_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    main()
