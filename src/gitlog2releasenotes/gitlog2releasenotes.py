'''
gitlog2releasenotes.gitlog2releasenotes -- convert list of (oneline) commits into release notes using a database populated with commits and issues.

@author:     Jim Lawson

@copyright:  2019 UC Berkeley. All rights reserved.

@license:    BSD-3-Clause

@contact:    ucbjrl@berkeley.edu
@deffield    updated: Updated
'''

from __future__ import print_function
import os
import re
import signal
import sys
import traceback
from argparse import ArgumentParser, FileType
from argparse import RawDescriptionHelpFormatter
from citSupport.monitorRepos import BaseRepo
from pymongo import MongoClient
from collections import OrderedDict

__all__ = []
__version__ = 0.1
__date__ = '2019-09-25'
__updated__ = '2019-09-25'

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
    print ('%s: signal %d' % (__name__, signum))
    if signum == signal.SIGTERM:
        doExit = True

class GitLogLine:
    def __init__(self):
        # Various regex's to match typical single-line commit logs
        self.lineRegex = re.compile(r"""^(?P<commit>([0-9A-Fa-f]+)) (?P<text>.*)$""")
        self.mergeRegex = re.compile(r"""^Merge pull request #(?P<pr>(\d+)) from """)
        self.mergeBranchRegex = re.compile(r"""^Merge (remote-tracking )?branch '[^']+' into \S+""")
        self.prRegex = re.compile(r"""^(?P<text>(.+))( \(#(?P<pr>(\d+))\))$""")

    # Analyze a commit log line and return a triple - (commit (sha as text), pull request id (int), text)
    def g2n(self, line):
        lm = self.lineRegex.match(line)
        if lm is None:
            raise CLIError('line doesn\'t match line regex - "%s"' % (line))
        p = None
        c = lm.group('commit')
        t = lm.group('text')
        mm = self.mergeRegex.match(t)
        if mm is None:
            mb = self.mergeBranchRegex.match(t)
            if mb:
                p = None
                t = None
            else:
                pm = self.prRegex.match(t)
                if pm:
                    p = int(pm.group('pr'))
                    t = pm.group('text')
        else:
            p = int(mm.group('pr'))
            t = None
        return (c, p, t)
    
    def test(self):
        mline = 'df0e0b1c Merge pull request #1022 from freechipsproject/cleanup-scaladoc'
        tline = 'dad4c236 Minor Scaladoc update (#1099)'
        (c, p, t) = self.g2n(mline)
        assert(p == 1022 and t is None)
        (c, p, t) = self.g2n(tline)
        assert(p == 1099 and t == 'Minor Scaladoc update')

class WorkContext:
    def __init__(self, database, file):
        self.database = database
        self.file = file

def doWork(wc, verbose):
    modName = __name__ + '.doWork'
    g2n = GitLogLine()
    # Connect to the database
    client = MongoClient()
    db = client[wc.database]
    # We assume the existence of at least two 'collections' (tables): pr_commits and issues
    commitDB = db['pr_commits']
    issueDB = db['issues']
    releaseNotes = {}
    releaseNotesNoPR = []
    # Use labels to categorize pull requests.
    # Each element maps a label string to a category (we may allocate the same category to various labels.
    # The order determines the reporting order.
    categories = OrderedDict([('API Modification', 'API Modification'), ('bug', 'Fix'), ('bugfix', 'Fix'), ('', 'Feature')])
    for category in set(categories.values()):
        releaseNotes[category] = {}
    for line in wc.file:
        # Set the default category
        category = 'Feature'
        # Parse the log line
        (commit, pr, text) = g2n.g2n(line)
        # If there isn't any text, this is a log line we're not interested in (i.e., a merge commit)
        if text:
            if pr is None:
                # If we couldn't find a pull request number in the log line, look for the matching commit (sha) in the database
                commitAbbrevMatch = re.compile('^' + commit)
                commitRecord = commitDB.find_one({ "sha" : {'$regex': commitAbbrevMatch}})
                if commitRecord is None:
                    # If we couldn't find a matching commit record based on the sha, try the commit message as a match
                    commitMessageMatch = re.compile('^' + re.escape(text))
                    commitRecord = commitDB.find_one({ "commit.message" : {'$regex': commitMessageMatch}})
                if commitRecord:
                    pr = commitRecord['pr']
            if pr:
                # We have a PR. Pull it out of the database
                rnText = ''
                title = ''
                pullRequest = issueDB.find_one({ "number" : pr})
                if pullRequest:
                    # Grab its important fields.
                    title = pullRequest['title']
                    for label in pullRequest['labels']:
                        if label['name'] in categories.keys():
                            category = categories[label['name']]
                    # Have we already encountered this PR?
                    if pr not in releaseNotes[category]:
                        # Eliminate any '\r' in the body.
                        body = pullRequest['body'].replace('\r', '')
                        # See if there's a **Release Notes** tag in the pull request body
                        rnTag1 = '\n**Release Notes**\n'
                        rnStartTag1 = body.find(rnTag1)
                        rnText = ''
                        rnType = 'c'
                        if rnStartTag1 > -1:
                            # Found a **Release Notes** tag. Do we need to skip instruction text as well?
                            rnIndex = rnStartTag1 + len(rnTag1)
                            rnTag2 = '<!--\nText from here to the end of the body will be considered for inclusion in the release notes for the version containing this pull request.\n-->'
                            if body.startswith(rnTag2, rnIndex):
                                rnIndex += len(rnTag2)
                            rnText = body[rnIndex:].strip()
                            if len(rnText) > 4:
                                # We have **Release Notes** for this PR. Use that as the text.
                                rnType = 'rn'
                                text = rnText
                    else:
                        rnType = releaseNotes[category][pr].keys()[0]
                else:
                    print('No PR %d in %s' % (pr, wc.database), file=sys.stderr)
                # Get the slot for this PR
                categorizedReleaseNotes = releaseNotes[category]
                if pr not in categorizedReleaseNotes:
                    # We haven't seen this PR before. 
                    categorizedReleaseNotes[pr] = {}
                    categorizedReleaseNotes[pr][rnType] = [title]
                    if text != title:
                        categorizedReleaseNotes[pr][rnType].append(text)
                elif rnType == 'c' and text not in categorizedReleaseNotes[pr][rnType]:
                    # If we've seen this PR before, but we don't have **Release Notes** for it, add the commit text if we don't already have it.
                    categorizedReleaseNotes[pr][rnType].append(text)
                   
            else:
                # No PR for this commit. Make sure it shows up somewhere
                releaseNotesNoPR.append((commit, text))

    # Output the no-PR commits
    for (c, t) in releaseNotesNoPR:
        asciiText = text.encode('ascii', 'replace').decode()
        print ('%s %s' % (c, asciiText))
    
    # Since we may have multiple labels mapped into the same category,
    # generate the set of legal labels (in the appropriate order) for this run.
    categoryLabels = []
    for category in categories:
        label = categories[category]        
        if releaseNotes[label] and label not in categoryLabels:
            categoryLabels.append(label)

    # Output a category label
    for label in categoryLabels:            
        if label != '':
            markdown = '### '
            print(markdown + label)
        # Output all the PRs under that label
        categorizedReleaseNotes = releaseNotes[label]
        for key in sorted(categorizedReleaseNotes):
            rnType = 'rn' if 'rn' in categorizedReleaseNotes[key] else 'c'
            text = '\n'.join(categorizedReleaseNotes[key][rnType])
            asciiText = text.encode('ascii', 'replace').decode()
            print ('(#%d) %s' % (key, asciiText))
            print ()
    return 0


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
  Copyright 2019 UC Berkeley. All rights reserved.

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
        parser.add_argument('-b', '--database', dest='database', required=True, help='database name')
        parser.add_argument(dest='files', help='files to be converted', type=FileType('r'), nargs='*')

        # Process arguments
        args = parser.parse_args()

        files = args.files
        verbose = args.verbose

        if verbose > 0:
            print("Verbose mode on")

        # Install the signal handler to catch SIGTERM
        signal.signal(signal.SIGTERM, sigterm)
        for afile in files:
            workContext = WorkContext(args.database, afile)
            doWork(workContext, verbose)
        return 0
 
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception, e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print (''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
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
        profile_filename = __name__ + '.' + 'profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    main()
