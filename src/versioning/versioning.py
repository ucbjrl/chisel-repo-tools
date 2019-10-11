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

versionFiles = {
    'build.sbt' : {
        'versionTag': r'[^[:alnum:]]version[[:space:]]*:=[[:space:]]*',
        'versionLineRegex' : re.compile(r'^(?P<prefix>.*\bversion\s*:=\s*")(?P<version>((?P<major>(\d+\.\d+))((\.(?P<minor>(\d+))(-(?P<releaseQualifier>(RC\d+)))?)|((-(?P<snapshotQualifer>(\d{6,6})))?-SNAPSHOT))))(?P<suffix>".*)$')
    },
    'build.sc' : {
        'versionTag': r'[^[:alnum:]]def[[:space:]]+publishVersion[[:space:]]*=[[:space:]]*',
        'versionLineRegex' : re.compile(r'^(?P<prefix>.*\bdef publishVersion\s*=\s*")(?P<version>((?P<major>(\d+\.\d+))((\.(?P<minor>(\d+))(-(?P<releaseQualifier>(RC\d+)))?)|((-(?P<snapshotQualifer>(\d{6,6})))?-SNAPSHOT))))(?P<suffix>".*)$')
    }
}

class WorkContext:
    def __init__(self, args, path):
        self.args = args
        self.path = path
        self.repo = BaseRepo(self.path)
        self.files = []
        self.version = None

    def currentMinorVersionFromGitTags(self, major: str) -> CNVersion:
        vt = None
        proc = subprocess.run(['git', 'tag', '-l'], cwd=self.path, capture_output=True, check=True, text=True)
        if proc.returncode == 0:
            majorMatch = re.compile(re.escape(major) + r'\.(?P<minor>(\d+))(-|\b)')
            tags = proc.stdout.split('\n')
            candidates = sorted(filter(majorMatch.search, tags), reverse=True)
            for c in candidates:
                vt = CNVersion(aString=c.strip('v'))
                if vt and vt.theInts[2] is not None:
                    break
        return vt

    def currentMinorVersionFromGitChangelog(self, major: str, baseFileName: str) -> CNVersion:
        vt = None
        regexes = versionFiles[baseFileName]
        versionTag = regexes['versionTag']
        versionLineRegex = regexes['versionLineRegex']
        # Look in the git change log for the first version with a minor revision
        minorRE = r'\.[0-9]+'
        minorRevisionRE = versionTag + '"' + re.escape(major) + minorRE
        proc = subprocess.run(['git', 'log', '-m', '-p', '-G' + minorRevisionRE, 'build.sbt'], cwd=self.path, capture_output=True, check=True, text=True)
        if proc.returncode == 0:
            changes = proc.stdout.split('\n')
            candidates = filter(versionLineRegex.search, changes)
            for c in candidates:
                line = c.rstrip('\n')
                lm = versionLineRegex.search(line)
                if lm:
                    versionString = lm.group('version')
                    vt = CNVersion(aString=versionString)
                    if vt and vt.theInts[2] is not None:
                        break
        return vt

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
            baseFilename = os.path.basename(f)
            regexes = versionFiles[baseFilename]
            versionTag = regexes['versionTag']
            versionLineRegex = regexes['versionLineRegex']
            myVersion = None
            with open(f, 'r') as input:
                for l in input:
                    line = l.rstrip('\n')
                    lm = versionLineRegex.search(line)
                    if lm:
                        versionString = lm.group('version')
                        myVersion = CNVersion(aString=versionString)
                        break
            if myVersion:
                print('{file}: {version} - {line}'.format(file=f, version=myVersion, line=line))
                # If we don't have a minor version, try and deduce it from git tags.
                if myVersion.theInts[2] is None:
                    deducedVersions = []
                    mismatchedVersions = []
                    major = '.'.join([str(i) for i in myVersion.theInts[CNVersion.MAJOR_SLICE]])
                    if self.repo:
                        vt = self.currentMinorVersionFromGitTags(major)
                        if vt:
                            deducedVersions.append(CNVersion(aVersion=myVersion, theInts=vt.theInts))
                        vt = self.currentMinorVersionFromGitChangelog(major, baseFilename)
                        if vt:
                            deducedVersions.append(CNVersion(aVersion=myVersion, theInts=vt.theInts))
                    if len(deducedVersions) > 0:
                        for v in deducedVersions[1:]:
                            if v != deducedVersions[0]:
                                mismatchedVersions.append(v)
                        if len(mismatchedVersions) == 0:
                            myVersion = deducedVersions[0]
                if version:
                    if myVersion != version:
                        raise CLIError('{f1} version {v1} != {f2} version {v2}'.format(f1=f1, v1=version, f2=f, v2=myVersion))
                else:
                    version = myVersion
                    f1 = f

        return version

    def writeVersion(self, version: str):
        """
        Update files containing module versions.
        """
        # Update any build.sbt or build.sc file with the specified version.
        dir = Path(self.path)
        self.files = [f for f in dir.glob('build.s*') if os.path.basename(f) == 'build.sbt' or os.path.basename(f) == 'build.sc']
        for f in self.files:
            baseFilename = os.path.basename(f)
            regexes = versionFiles[baseFilename]
            versionTag = regexes['versionTag']
            versionLineRegex = regexes['versionLineRegex']
            inputName = str(f)
            outputName = inputName + '.versioning'
            w = Path(outputName)
            update = False
            with open(f, 'r') as input, open(w, 'w') as output:
                for l in input:
                    line = l.rstrip('\n')
                    lm = versionLineRegex.match(line)
                    if lm:
                        prefix = lm.group('prefix')
                        suffix = lm.group('suffix')
                        line = prefix + version + suffix
                        update = True
                    print(line, file=output)
            if update:
                os.rename(inputName, inputName + '.bak')
                os.rename(outputName, inputName)
            else:
                os.remove(outputName)



def doWork(wc):
    version = wc.determineVersion()
    if wc.args.command == 'bump-min':
        bumpedVersion = version.bumpMinor()
        versionString =  bumpedVersion.releaseVersion() if wc.args.release else bumpedVersion.snapshotVersion()
        print('o: %s, b:%s' % (version, versionString))
        if wc.args.update:
            wc.writeVersion(versionString)
    elif wc.args.command == 'bump-maj':
        bumpedVersion = version.bumpMajor()
        versionString = bumpedVersion.releaseVersion() if wc.args.release else bumpedVersion.snapshotVersion()
        print('o: %s, b:%s' % (version, versionString))
        if wc.args.update:
            wc.writeVersion(versionString)

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
        parser.add_argument('-s', '--snapshot', dest='snapshot', action='store', nargs='?', help='generate snapshot version')
        parser.add_argument('-r', '--release', dest='release', action='store', nargs='?', help='generate release version')
        parser.add_argument('-u', '--update', dest='update', action='store_true', help='Update changed files')
        parser.add_argument(dest='command', choices=['bump-min', 'bump-maj'])
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
