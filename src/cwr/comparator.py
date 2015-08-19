'''
Created on Sep 18, 2014

@author: jrl
'''

import os
import re
from splitTokens import splitTokens
import stat
import sys

__all__ = []
__version__ = 0.1
__date__ = '2014-09-18'
__updated__ = '2014-09-18'

DEBUG = 1
TESTRUN = 0
PROFILE = 0

class ComparatorError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg, lineNo = None, lineString = None):
        super(ComparatorError).__init__(type(self))
        self.msg = "E: %s" % msg
        self.lineNo = lineNo
        self.lineString = lineString
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

class Comparator(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        '''
        self.substitutions = {}
        self.tokenizer = splitTokens()
        self.allowedDifferencePrefixRegex = re.compile(r"""[RT]""")
        self.EOLRegex = re.compile(r""".*\n""")

    def addSubstitutions(self, substitutions, lineNo, lineString):
        '''
        Add new substitutions to the map. If we already have a different substitute for any element,
        raise an exception, otherwise return None (indicating success)
        '''
        for (original, substitute) in substitutions.items():
            if self.substitutions.has_key(original):
                oldSubstitution = self.substitutions[original]
                if oldSubstitution['value'] != substitute:
                    definedLineNo = oldSubstitution['lineNo']
                    definedLineString = oldSubstitution['lineString']
                    raise ComparatorError('illegal substitution - "%s" - "%s" already exists for "%s", from line %d, "%s"' % (substitute, oldSubstitution['value'], original, definedLineNo, definedLineString), lineNo, lineString)
            else:
                self.substitutions[original] = dict (value=substitute, lineNo=lineNo, lineString=lineString )
        return None
    
    def substitutesFromLine(self, lineNo, originalLine, testLine):
        '''
        Compare a line from the original and the test strings and return a likely list of substitutions
        to get them to match.
        '''
        # Try the simplest test first.
        if originalLine == testLine:
            return None
        substitutions = {}
        # The lines are different. Tokenize them and compare tokens.
        originalTokens = self.tokenizer.tokenize(originalLine)
        testTokens = self.tokenizer.tokenize(testLine)
        for original, test in zip(originalTokens, testTokens):
            if original != test:
                # Tokens don't match. Currently, we only allow mismatches for registers and temporaries.
                if original[0] == test[0] and self.allowedDifferencePrefixRegex.match(original):
                    substitutions[test] = original
                else:
                    raise ComparatorError('illegal substitution - can\'t substitute "%s" for "%s"' % (original, test), lineNo, testLine)
        return substitutions

    def generateSubstitutes(self, original, test):
        # Easy test first.
        if original == test:
            return None
        originalLines = original.split("\n")
        testLines = test.split("\n")
        # We should have the same number of lines of each.
        if len(originalLines) != len(testLines):
            return ComparatorError('original(%d) and test(%d) line count differ' % (len(originalLines), len(testLines)))
        lineNo = 0
        for originalLine, testLine in zip(originalLines, testLines):
            lineNo += 1
            substitutions = self.substitutesFromLine(lineNo, originalLine, testLine)
            if substitutions != None:
                self.addSubstitutions(substitutions, lineNo, testLine)

        return len(self.substitutions)

    def compareWithSubstitutions(self, original, test):
        originalTokens = self.tokenizer.tokenize(original)
        testTokens = self.tokenizer.tokenize(test)
        if len(originalTokens) != len(testTokens):
            return ComparatorError('original(%d) and test(%d) token count differ' % (len(originalTokens), len(testTokens)))
        # We maintain the fiction that we're doing line by line comparisons.
        originalLine = ""
        testLine = ""
        # Generate the substituted test tokens
        for original, test in zip(originalTokens, testTokens):
            originalLine += original
            testLine += test
            if self.substitutions.has_key(test):
                test = self.substitutions[test]['value']
            if original != test:
                return ComparatorError('"%s" != "%s"' % (originalLine, testLine))
            # If this is a newline, reset our accumulated line
            if self.EOLRegex.match(original) != None:
                originalLine = ""
            # NOTE: This is safe since we don't allow substitution of none
            # (R|T)words, i.e., if the original test token was EOL, it will
            # still be EOL.
            if self.EOLRegex.match(test) != None:
                testLine = ""
        return None

def compareFiles(masters, tests):
    for master, test in zip(masters, tests):
        original = open(master).read()
        test = open(test).read()
        comparator = Comparator()
        result = comparator.generateSubstitutes(original, test)
        # Do they match?
        if result is None:
            return 0
        elif isinstance(result, ComparatorError):
            return result
        # They don't match, but we have some substitutions to try.
        result = comparator.compareWithSubstitutions(original, test)
        if isinstance(result, ComparatorError):
            return result
    return 0

def main(argv=None):
    '''Command line options.'''
    from argparse import ArgumentParser
    from argparse import RawDescriptionHelpFormatter

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
  Copyright 2014 UC Berkeley. All rights reserved.

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
        parser.add_argument('-m', '--master', dest="master", help="gold master directory", action='store', default=None)
        parser.add_argument('-t', '--test', dest="test", help="test directory",  action='store', default=None)
        parser.add_argument(dest="files", help="files to compare",  action='store', default=None, nargs='*')

        # Process arguments
        args = parser.parse_args()

        verbose = args.verbose
        if verbose > 0:
            print("Verbose mode on")

        masters = []
        tests = []
        if args.master is None and args.test is None:
            if len(args.files) != 2:
                sys.stderr.write(program_name + ": " + "need two files to compare" + "\n")
                return 2
            masters.append(args.files[0])
            tests.append(args.files[1])
        else:
            if not (os.path.isdir(args.master) and os.path.isdir(args.test)):
                sys.stderr.write(program_name + ": " + "master and test must be directories" + "\n")
                return 2
            files = args.files
            if files is None or len(files) == 0:
                files = os.listdir(args.master)
            for f in files:
                masters.append(os.path.join(args.master, f))
                tests.append(os.path.join(args.master, f))

        result = compareFiles(masters, tests)
        if isinstance(result, ComparatorError):
            sys.stderr.write(program_name + ": " + repr(result) + "\n")
            return 1
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
        profile_filename = 'cwr.cwr_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    main()
