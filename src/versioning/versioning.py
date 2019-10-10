'''
versioning.versioning -- module to support version manipulation.

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
import subprocess
from pathlib import Path
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from version.Version import CNVersion
from citSupport.monitorRepos import BaseRepo

__all__ = []
__version__ = 0.1
__date__ = '2019-10-07'
__updated__ = '2019-10-07'

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

class WorkContext:
    def __init__(self, args, path):
        self.args = args
        self.path = path
        self.repo = BaseRepo(self.path)
        self.files = []
        self.version = None

#    def currentMinorVersionFromGitTags(self):

    def determineVersion(self) -> CNVersion:
        """
        Determine the version of a module.
        :return: an CNVersion object or None if the version can not be determined.
        """
        version = None
        f1 = None
        line = None
        # If there is a build.sbt or build.sc file, we may be able to extract the version using sbt
        dir = Path(self.path)
        self.files = [f for f in dir.glob('build.s*') if os.path.basename(f) == 'build.sbt' or os.path.basename(f) == 'build.sc']
        versionTag = None
        for f in self.files:
            if os.path.basename(f) == 'build.sbt':
                versionTag = r'[^[:alnum:]]version[[:space:]]*:=[[:space:]]*'
                versionLineRegex = re.compile(r'\bversion\s*:=\s*"(?P<version>((?P<major>(\d+\.\d+))((\.(?P<minor>(\d+))(-(?P<releaseQualifier>(RC\d+)))?)|((-(?P<snapshotQualifer>(\d{6,6})))?-SNAPSHOT))))"')
            elif os.path.basename(f) == 'build.sc':
                versionTag = r'[^[:alnum:]]def[[:space:]]+publishVersion[[:space:]]*=[[:space:]]*'
                versionLineRegex = re.compile(r'def publishVersion\s*=\s*"(?P<version>((?P<major>(\d+\.\d+))((\.(?P<minor>(\d+))(-(?P<releaseQualifier>(RC\d+)))?)|((-(?P<snapshotQualifer>(\d{6,6})))?-SNAPSHOT))))"')
            with open(f, 'r') as input:
                for l in input:
                    line = l.rstrip('\n')
                    lm = versionLineRegex.search(line)
                    if lm:
                        versionString = lm.group('version')
                        myVersion = CNVersion(aString=versionString)
                        if version:
                            if myVersion != version:
                                raise CLIError('{f1} version {v1} != {f2} version {v2}'.format(f1=f1, v1=version, f2=f, v2=myVersion))
                        else:
                            version = myVersion
                            f1 = f
                        break
            print('{file}: {version} - {line}'.format(file=f, version=version, line=line))
        if version:
            # If we don't have a minor version, try and deduce it from git tags.
            if version.theInts[2] is None and False:
                major = '.'.join([str(i) for i in version.theInts[CNVersion.MAJOR_SLICE]])
                if self.repo:
                    tags = []
                    proc = subprocess.run(['git', 'tag', '-l'], cwd=dir, capture_output=True, check=True, text=True)
                    if proc.returncode == 0:
                        majorMatch = re.compile(re.escape(major) + r'\.(?P<minor>(\d+))(-|\b)')
                        tags = proc.stdout.split('\n')
                        candidates = sorted(filter(majorMatch.search, tags), reverse=True)
                        vt = None
                        for c in candidates:
                            vt = CNVersion(aString=c.strip('v'))
                            if vt and vt.theInts[2] is not None:
                                break
                        if vt:
                            version = CNVersion(aVersion=version, theInts=vt.theInts)
            # If we don't have a minor version, try and deduce it from git change logs.
            if version.theInts[2] is None:
                major = '.'.join([str(i) for i in version.theInts[CNVersion.MAJOR_SLICE]])
                if self.repo:
                    tags = []
                    # Look in the git change log for the first version with a minor revision
                    versionTag = r'[^[:alnum:]]version[[:space:]]*:=[[:space:]]*'
                    minorRE = r'\.[0-9]+'
                    minorRevisionRE = versionTag + '"' + re.escape(major) + minorRE
                    versionLineRegex = re.compile(r'\bversion\s*:=\s*"(?P<version>((?P<major>(\d+\.\d+))((\.(?P<minor>(\d+))(-(?P<releaseQualifier>(RC\d+)))?)|((-(?P<snapshotQualifer>(\d{6,6})))?-SNAPSHOT))))"')
                    proc = subprocess.run(['git', 'log', '-m', '-p', '-G' + minorRevisionRE, 'build.sbt'], cwd=dir, capture_output=True, check=True, text=True)
                    if proc.returncode == 0:
                        changes = proc.stdout.split('\n')
                        candidates = filter(versionLineRegex.search, changes)
                        vt = None
                        for c in candidates:
                            line = c.rstrip('\n')
                            lm = versionLineRegex.search(line)
                            if lm:
                                versionString = lm.group('version')
                                vt = CNVersion(aString=versionString)
                                if vt and vt.theInts[2] is not None:
                                    break
                        if vt:
                            version = CNVersion(aVersion=version, theInts=vt.theInts)

        return version

def doWork(wc):
    bumpMin(wc)

def bumpMin(wc):
    version = wc.determineVersion()
    print(version.releaseVersion())
    print(version.snapshotVersion())
    #    versionLineRegex = re.compile(r'''=\s*"(?P<major>(\d+\.\d+))((?P<minor>\d+)(((-(?P<releaseQualifier>)RC\d+))|((-(?P<snapshotQualifer>\d{6,6}))?-SNAPSHOT)))''')
    #    versionLineRegex = re.compile(r'.+=\s*"(?P<major>(\d+\.\d+))((?P<minor>(\d+))(((-(?P<releaseQualifier>)(RC\d+))?|((-(?P<snapshotQualifer>(\d{6,6}))?-SNAPSHOT")))))')
    # Find the local git repo from the path
    versionLineRegex = re.compile(r'(?!scala)[Vv]ersion\s*:?=\s*"(?P<major>(\d+\.\d+))((\.(?P<minor>(\d+))(-(?P<releaseQualifier>(RC\d+)))?)|((-(?P<snapshotQualifer>(\d{6,6})))?-SNAPSHOT"))')


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
        parser.add_argument('-p', '--snapshotQualifer', dest='snapshotQualifer', help='set snapshotQualifer (usually DDMMYY) for SNAPSHOT')
        parser.add_argument('-s', '--releaseQualifier', dest='releaseQualifier', help='set releaseQualifier (usually RCn) for release')
        parser.add_argument('-r', '--release', dest='release', help='set version (Z.Y.Z) for release')
        parser.add_argument(dest='command', choices=['bump-min', 'bump-maj', 'snapshot', 'release'], nargs=1)
        parser.add_argument(dest='paths', help='paths to search for files to be manipulated', nargs='*')

        # Process arguments
        args = parser.parse_args()

        verbose = args.verbose

        if verbose > 0:
            print("Verbose mode on")

        # Install the signal handler to catch SIGTERM
        signal.signal(signal.SIGTERM, sigterm)
        for aPath in args.paths:
            workContext = WorkContext(args, aPath)
            doWork(workContext)
        return 0

    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
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
        profile_filename = __name__ + '.' + 'profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    main()
