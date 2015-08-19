"""
Created on Sep 18, 2014

@author: jrl
'''
import re

class splitTokens {
    """
    Token splitter - split a string into 'tokens'
    '''


    val self.tokenRegExString = r"""(\W+)"""
    val self.tokenRegEx = re.compile(tokenRegExString)
    def __init__() {
        """
        '''
    }

    def tokenize(str) {
        return tokenRegEx.split(str)
    }
}
"""
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
__date__ = "2014-09-18"
__updated__ = "2014-09-18"

DEBUG = 1
TESTRUN = 0
PROFILE = 0

class ComparatorError (amsg: String, alineno: Option[Int] = None, alinestring: Option[String] = None) extends Exception {
    """Generic exception to raise and log different fatal errors."""
    val msg = "E: %s" format amsg
    val lineNo = alineNo
    val lineString = alineString
    def toString = msg
}

class Comparator {
    var substitutions = HashMap[String, String]()
    val self.tokenizer = splitTokens()
    val self.allowedDifferencePrefixRegex = re.compile(r"""[RT]""")
    val self.EOLRegex = re.compile(r""".*\n""")

    /*
        Add new substitutions to the map. If we already have a different substitute for any element,
        raise an exception, otherwise return None (indicating success)
	*/

    def addSubstitutions(newSubstitutions: Map[String,String], lineNo: Int, lineString; String) {
        for ((original, substitute) <- newSubstitutions) {
            if (this.substitutions.contains(original)) {
                val (oldValue, oldLineNo, oldLineString) = substitutions(original)
                if (oldValue != substitute) {
                    throw ComparatorError("illegal substitution - "%s" - "%s" already exists for "%s", from line %d, "%s"" format (substitute, oldValue, original, oldLineNo, oldLineString), lineNo, lineString)
                }
            } else {
	      substitutions(original) = (substitute, lineNo, lineString )
	    }
        }
    }
    
    /*
        Compare a line from the original and the test strings and return a likely list of substitutions
        to get them to match.
      */
    def substitutesFromLine(lineNo: Int, originalLine: String, testLine: String): Option[HashMap[String, String]] = {
        // Try the simplest test first.
        if (originalLine == testLine)
            return None
        val substitutions = HashMap[String, String]()
        // The lines are different. Tokenize them and compare tokens.
        val originalTokens = tokenizer.tokenize(originalLine)
        val testTokens = tokenizer.tokenize(testLine)
        for (original, test <- zip(originalTokens, testTokens)) {
            if (original != test) {
                // Tokens don't match. Currently, we only allow mismatches for registers and temporaries.
                if (original(0) == test(0) && allowedDifferencePrefixRegex.match(original))
                    substitutions(test) = original
                else
                    raise ComparatorError("illegal substitution - can\'t substitute "%s" for "%s"" format (original, test), lineNo, testLine)
            }
        }
        return substitutions
    }

    def generateSubstitutes(original: String, test: String): Option[Int] = {
        // Easy test first.
        if (original == test)
            return None
        val originalLines = original.split("\n")
        val testLines = test.split("\n")
        // We should have the same number of lines of each.
        if (originalLines.length != testLines.length)
            return ComparatorError("original(%d) and test(%d) line count differ" format (originalLines.length, testLines.length))
        var lineNo = 0
        for (originalLine, testLine <- zip(originalLines, testLines)) {
            lineNo += 1
            val substitutions = substitutesFromLine(lineNo, originalLine, testLine)
            if (substitutions != null)
                addSubstitutions(substitutions, lineNo, testLine)
        }

        return substitutions.length
    }

    def compareWithSubstitutions(original, test) {
        val originalTokens = tokenizer.tokenize(original)
        val testTokens = tokenizer.tokenize(test)
        if (originalTokens.length != testTokens.length)
            return ComparatorError("original(%d) and test(%d) token count differ" format (originalTokens.length, testTokens.length))
        // We maintain the fiction that we're doing line by line comparisons.
        var originalLine = ""
        var testLine = ""
        // Generate the substituted test tokens
        for (original, test <- zip(originalTokens, testTokens)) {
            originalLine += original
            testLine += test
            if (substitutions.has_key(test))
                test = substitutions(test)["value"]
            if (original != test)
                return ComparatorError(""%s" != "%s"" format (originalLine, testLine))
            // If this is a newline, reset our accumulated line
            if (EOLRegex.match(original) != null)
                originalLine = ""
            // NOTE: This is safe since we don't allow substitution of none
            // (R|T)words, i.e., if the original test token was EOL, it will
            // still be EOL.
            if (EOLRegex.match(test) != null)
                testLine = ""
        }
        return null
    }
}

def compareFiles(masters, tests) {
    for (master, test <- zip(masters, tests)) {
        val original = open(master).read()
        val test = open(test).read()
        val comparator = Comparator()
        var result = comparator.generateSubstitutes(original, test)
        // Do they match?
        if (result == null)
            return 0
        else if (isinstance(result, ComparatorError))
            return result
        // They don't match, but we have some substitutions to try.
        result = comparator.compareWithSubstitutions(original, test)
        if (isinstance(result, ComparatorError))
            return result
    }
    return 0
}

def main(argv=null) {
    """Command line options."""
    from argparse import ArgumentParser
    from argparse import RawDescriptionHelpFormatter

    if (argv == null)
        argv = sys.argv
    else
        sys.argv.extend(argv)

    val program_name = os.path.basename(sys.argv(0))
    val program_version = "v%s" format __version__
    val program_build_date = str(__updated__)
    val program_version_message = "%%(prog)s %s (%s)" format (program_version, program_build_date)
    val program_shortdesc = __import__("__main__").__doc__.split("\n")[1]
    val program_license = """%s

  Created by Jim Lawson on %s.
  Copyright 2014 UC Berkeley. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' format (program_shortdesc, str(__date__))
    try {
        // Setup argument parser
        val parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument("-V", "--version", action="version", version=program_version_message)
        parser.add_argument("-m", "--master", dest="master", help="gold master directory", action="store", default=null)
        parser.add_argument("-t", "--test", dest="test", help="test directory",  action="store", default=null)
        parser.add_argument(dest="files", help="files to compare",  action="store", default=null, nargs='*')

        // Process arguments
        val args = parser.parse_args()

        val verbose = args.verbose
        if (verbose > 0)
            print("Verbose mode on")

        val masters = []
        val tests = []
        if (args.master == null && args.test == null) {
            if (args.files.length != 2) {
                sys.stderr.write(program_name + ": " + "need two files to compare" + "\n")
                return 2
            }
            masters.append(args.files(0))
            tests.append(args.files(1))
        }
        else {
            if (!(os.path.isdir(args.master) && os.path.isdir(args.test))) {
                sys.stderr.write(program_name + ": " + "master and test must be directories" + "\n")
                return 2
            }
            var files = args.files
            if (files == null || files.length == 0)
                files = os.listdir(args.master)
            for (f <- files) {
                masters.append(os.path.join(args.master, f))
                tests.append(os.path.join(args.master, f))
            }
        }

        val result = compareFiles(masters, tests)
        if (isinstance(result, ComparatorError)) {
            sys.stderr.write(program_name + ": " + repr(result) + "\n")
            return 1
        }
        return 0
    }

    catch KeyboardInterrupt {
        //## handle keyboard interrupt ###
        return 0
    }
    catch Exception, e {
        if (DEBUG || TESTRUN)
            raise(e)
        val indent = program_name.length * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2
    }
}
   
if (__name__ == "__main__")
    if (DEBUG)
        sys.argv.append("-v")
    if (TESTRUN) {
        import doctest
        doctest.testmod()
    }
    if (PROFILE) {
        import cProfile
        import pstats
        profile_filename = "cwr.cwr_profile.txt"
        cProfile.run("main()", profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats("cumulative")
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    }
    main()
