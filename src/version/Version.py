'''
version.Version -- A class providing a definition of and access to the Chisel normal version format

@author:     Jim Lawson

@copyright:  2019 UC Berkeley. All rights reserved.

@license:    BSD-3-Clause

@contact:    ucbjrl@berkeley.edu
@deffield    updated: 2019-10-08
'''

import sys
import os
import re
import signal
import traceback
import copy
from typing import List

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.1
__date__ = '2019-10-08'
__updated__ = '2019-10-08'

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

class CNVersion:
    nComponents = 3
    MAJOR_SLICE = slice(2)
    MINOR_SLICE = slice(2, nComponents)
    versionRegex = re.compile(r'"?(?P<major>(\d+\.\d+))((\.(?P<minor>(\d+))(-(?P<releaseQualifier>(RC\d+)))?)|((-(?P<snapshotQualifer>(\d{6,6})))?-SNAPSHOT))"?')

    @staticmethod
    def valsToString(theInts:List[int]) -> str:
        theString = '.'.join([str(v) for v in theInts if v is not None])
        return theString

    def bumpMajor(self) -> 'CNVersion':
        res = copy.copy(self)
        res.theInts[1] += 1
        res.theInts[2] = 0
        return res

    def bumpMinor(self) -> 'CNVersion':
        res = copy.copy(self)
        res.theInts[2] += 1
        return res

    def releaseVersion(self) -> str:
        s = CNVersion.valsToString(self.theInts)
        s += ( '-' + self.releaseQualifier) if self.releaseQualifier else ''
        return s

    def snapshotVersion(self) -> str:
        s = CNVersion.valsToString(self.theInts[CNVersion.MAJOR_SLICE])
        s += (( '-' + self.snapshotQualifer) if self.snapshotQualifer else '') + '-SNAPSHOT'
        return s

    def __init__(self, **kwargs):
        # Initialize defaults
        self.snapshotQualifer = None
        self.releaseQualifier = None
        self.theInts = [None] * CNVersion.nComponents
        aString = kwargs.get('aString', None)
        aVersion = kwargs.get('aVersion', None)
        theInts = kwargs.get('theInts', None)
        snapshotQualifer = kwargs.get('snapshotQualifier', None)
        releaseQualifier = kwargs.get('releaseQualifier', None)

        if aString and aVersion:
            raise 'only one of string or an existing CNVersion should be supplied: %s, %s' % (aString, aVersion)
        if aString:
            vrm = CNVersion.versionRegex.match(aString)
            if vrm:
                versionDict = vrm.groupdict()
                if not 'major' in versionDict:
                    raise CLIError('couldn\'t find major version: "%s"' % (aString))
                major = versionDict.get('major')
                m = major.split('.')
                for i in range(2):
                    self.theInts[i] = int(m[i])
                minor = versionDict.get('minor')
                self.theInts[2] = int(minor) if minor else None
                self.snapshotQualifer = versionDict.get('snapshotQualifer')
                self.releaseQualifier = versionDict.get('releaseQualifier')
            else:
                raise CLIError('couldn\'t parse string as a version: "%s"' % (aString))
        elif aVersion:
            for attribute in self.__dict__.keys():
                setattr(self, attribute, copy.deepcopy(getattr(aVersion, attribute, None)))

        for attribute in kwargs.keys():
            if attribute in self.__dict__.keys():
                setattr(self, attribute, copy.deepcopy(kwargs.get(attribute)))

        if theInts:
            if len(theInts) != 3:
                raise CLIError('a list of 3 ints should be supplied: "%s"' % (','.join([str(i) for i in theInts])))
            for i in range(3):
                self.theInts[i] = theInts[i]
        if snapshotQualifer:
            self.snapshotQualifer = snapshotQualifer
        if releaseQualifier:
            self.releaseQualifier = releaseQualifier

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, CNVersion):
            equal = True
            for i in range(CNVersion.nComponents):
                equal &= self.theInts[i] == other.theInts[i]
                if not equal:
                    break
            if equal:
                equal &= self.snapshotQualifer == other.snapshotQualifer
            if equal:
                equal &= self.releaseQualifier == other.releaseQualifier
            return equal
        else:
            return NotImplemented

    def __hash__(self):
        """Overrides the default implementation"""
        return hash(tuple(sorted(self.__dict__.items())))

    def __repr__(self) -> str:
        s = CNVersion.valsToString(self.theInts)
        s += ( '-' + self.releaseQualifier) if self.releaseQualifier else ''
        s += (( '-' + self.snapshotQualifer) if self.snapshotQualifer else '') + '-SNAPSHOT'
        return s


def main(argv=None): # IGNORE:C0111

    def sigterm(signum, frame):
        global doExit
        print ('%s: signal %d' % (__name__, signum))
        if signum == signal.SIGTERM:
            doExit = True

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

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument("-s", "--setString", dest="string", help="version as dotted strinf", metavar="str" )
        parser.add_argument("-i", "--setInts", dest="ints", help="version as list of ints", metavar="str" )
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
 
        # Process arguments
        args = parser.parse_args()

        verbose = args.verbose
        if verbose > 0:
            print("Verbose mode on")

        aString = args.string
        theInts = [int(x) for x in args.ints.split('.', CNVersion.nComponents)] if args.ints else None



        # Install the signal handler to catch SIGTERM
        signal.signal(signal.SIGTERM, sigterm)

        version = CNVersion(aString = aString, theInts = theInts)
        print(version)
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
        profile_filename = 'version.Version_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())