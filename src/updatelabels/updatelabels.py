'''
updatelabels.updatelabels -- get labels for a repository

@author:     Jim Lawson

@copyright:  2019 UC Berkeley. All rights reserved.

@license:    BSD

@contact:    ucbjrl@berkeley.edu
@deffield    updated: 2019-10-21
'''

import sys
import os
import traceback

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from citSupport.monitorRepos import BaseRepo

__all__ = []
__version__ = 0.1
__date__ = '2019-10-21'
__updated__ = '2019-10-21'

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
    issueText = {
        'Type of change' : {'Bug report': ('improvement', 'bug fix'), 'Feature request': ('improvement', 'new feature'), 'Other enhancement': None},
        'Impact' : {'no functional change': None, 'API addition (no impact on existing code': ('API impact', 'addition'), 'API modification': ('API impact', 'breaking')},
        'Development Phase' : {'proposal': ('status', 'claim me!'), 'implementation': ('status', 'in progress')}
    }
    oldLabelMap = {
        'API Addition': ('API impact', 'addition'),
        'API Addition (no impact on existing code)': ('API impact', 'addition'),
        'API Modification': ('API impact', 'breaking'),
        'Challenge Issue': ('level', 'challenge'),
        'DO NOT MERGE': ('merge strategy', 'do not merge'),
        'Feature Request': ('improvement', 'new feature'),
        'Implementation': None,
        'Merge Commit Please': None,
        'Merge with merge commit': ('merge strategy', 'merge commit'),
        'Please Merge': None,
        'Request': None,
        'Request For Comment': None,
        'Squash and merge': ('merge strategy', 'squash and merge'),
        'bug': ('improvement', 'bug fix'),
        'bugfix': ('improvement', 'bug fix'),
        'cleanup': ('improvement', 'code cleanup'),
        'code improvement': ('improvement', 'code cleanup'),
        'documentation needed': None,
        'duplicate': ('status', 'duplicate'),
        'enhancement': ('improvement', 'new feature'),
        'feature': ('improvement', 'new feature'),
        'feature request': ('improvement', 'new feature'),
        'good first issue': ('level', 'first'),
        'help wanted': None,
        'high priority': None,
        'invalid':  ('status', 'won\'t fix'),
        'long-term': None,
        'low priority': None,
        'medium priority': None,
        'question': None,
        'release issue': None,
        'requesting review': None,
        'strict-semantics': None,
        'top priority': None,
        'usability': None,
        'wontfix': ('status', 'won\'t fix')
    }
    newLabels = {
        'status': tuple(['claim me!', 'in progress', 'paused', 'won\'t fix', 'duplicate']),
        'bounty': tuple(['libation compensation', 'Chisel T-shirt', 'cool sticker']),
        'merge strategy': tuple(['do not merge', 'squash and merge', 'merge commit']),
        'level': tuple(['first', 'normal', 'challenge']),
        'improvement': tuple(['performance', 'documentation', 'refactoring', 'code cleanup', 'backend generation', 'new feature', 'bug fix']),
        'code generation': None,
        'API impact': tuple(['breaking', 'addition', 'deprecation', 'removal'])
    }
    oldLabels = {
    }

    @staticmethod
    def label(category, selector):
        return ChiselLabels.labels[category][selector]

def updatelabels(repoPath):
    modName = __name__ + '.updatelabels'

    baseRepo = BaseRepo(repoPath)
    if baseRepo is None:
        exit(1)
    baseRepo.connect()
    repo = baseRepo.remoterepo

#    outputFilename = repoPath + '.labels'
    labels = list(repo.labels())
#    with open(outputFilename, 'w') as output:
    print(repoPath)
    for label in labels:
        d = label.as_dict()
        d['repo'] = repoPath
        oldLabel = d['name']
        oldColor = d['color']
        oldDescription = d['description']
        if not oldLabel in ChiselLabels.oldLabels.keys():
            ChiselLabels.oldLabels[oldLabel] = {}
            ChiselLabels.oldLabels[oldLabel]['colors'] = []
            ChiselLabels.oldLabels[oldLabel]['descriptions'] = []
        if not oldColor in [l['color'] for l in ChiselLabels.oldLabels[oldLabel]['colors']]:
            ChiselLabels.oldLabels[oldLabel]['colors'].append(d)
        if oldDescription is not None and oldDescription != '' and not oldDescription in [l['description'] for l in ChiselLabels.oldLabels[oldLabel]['descriptions']]:
            ChiselLabels.oldLabels[oldLabel]['descriptions'].append(d)

def reportCollisions():
    modName = __name__ + '.reportCollisions'

    for name, refs in ChiselLabels.oldLabels.items():
        labels = refs['colors']
        if len(labels) > 1:
            nColors = len(labels)
            colors = [l['color'] for l in labels]
            collissions = [("%s (%s)" % (l['color'], l['repo'])) for l in labels]
            r = b = g = 0
            for color in colors:
                val = bytes.fromhex(color)
                r += val[0]
                g += val[1]
                b += val[2]
            r = int(r/nColors)
            g = int(g/nColors)
            b = int(b/nColors)
            newColor = (r << 16 ) | (g << 8) | (b)
            print('color collision: %s %s -> %s' % (name, ', '.join(collissions), hex(newColor)))
        labels = refs['descriptions']
        if len(labels) > 1:
            collissions = [("%s (%s)" % (l['description'], l['repo'])) for l in labels]
            print('description collision: %s %s' % (name, '; '.join(collissions)))

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
        parser.add_argument(dest='paths', help='paths to local clones of github repositories)', nargs='*')

        # Process arguments
        args = parser.parse_args()

        verbose = args.verbose

        if verbose > 0:
            print("Verbose mode on")

        for path in args.paths:
            updatelabels(path)
        reportCollisions()
        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except CLIError as e:
        sys.stderr.write(program_name + ": " + e.msg + "\n")
        sys.exit(1)
    except Exception as e:
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
        profile_filename = 'updatelabels.updatelabels_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())