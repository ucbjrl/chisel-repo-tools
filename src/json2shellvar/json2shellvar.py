# encoding: utf-8
'''
json2shellvar.json2shellvar -- convert JSON to shell variable definitions

json2shellvar.json2shellvar is a program to parse JSON data and extract values suitable for assignment to shell variables.

It defines classes_and_methods

@author:     ucbjrl

@copyright:  2018 The Regents of the University of California (Regents). All rights reserved.

@license:    BSD-3

@contact:    ucbjrl@berkeley.edu
@deffield    updated: Updated
'''

import sys
import os
import re
import json
import requests
from urlparse import urlparse

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.1
__date__ = '2018-06-25'
__updated__ = '2018-06-25'

DEBUG = 0
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

# Parse a list of variable assignments, such as PARENT_BRANCH=base.sha,
#  and return a string consisting of shell compatible assignments PARENT_BRANCH="xyx"
#  where "xyz" is the value of the JSON element, "" if not found.
def doWork(assignments, jsonData):
    result = []
    whitespace = re.compile(r"\s")
    quote = re.compile(r"(.)\"")
    for assignment in assignments:
        variableAssignment = str.split(assignment, "=", 1)
        jsonFields = str.split(variableAssignment[1], ".")
        data = jsonData
        for field in jsonFields:
            if data.get(field):
                data = data.get(field)
            else:
                data = ""
                break
        delim = ""
        if whitespace.search(data):
            delim = '"'
            data = str.replace(data, '"', '\\"')
            
        result.append("{0}={1}{2}{1}".format(variableAssignment[0], delim, data))
    return ' '.join(result)
        
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

  Created by ucbjrl on %s.
  Copyright 2018 The Regents of the University of California. All rights reserved.

  Licensed under the 3-clause BSD license.
  https://opensource.org/licenses/BSD-3-Clause

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument("-j", "--json", dest="json", help="file or URL containing JSON data")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument(dest="variables", help="shell variable assignments", nargs='+')

        # Process arguments
        args = parser.parse_args()

        variables = args.variables
        verbose = args.verbose
        jsonSource = args.json

        if verbose:
            print("Verbose mode on")

        jsonData = {}
        # Are we given any JSON source?
        if jsonSource is None or jsonSource == "-":
            sys.stderr.write("({0}: reading from stdin ...".format(program_name))
            sys.stderr.flush()
            text = sys.stdin.read()
            sys.stderr.write(" )\n")
            jsonData = json.loads(text)
        elif urlparse(jsonSource).scheme in ('http', 'https'):
            response = requests.get(jsonSource)
            jsonData = response.json()
        else:
            jsonData = json.load(open(jsonSource, 'r'))

        result = doWork(variables, jsonData)
        print(result)
        return 0
    
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception as e:
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
        profile_filename = 'json2shellvar.json2shellvar_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())