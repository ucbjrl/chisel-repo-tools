#!/usr/bin/env python
# encoding: utf-8
'''
sbttest.results -- generate CSV file from sbt test output

@author:     Jim Lawson

@copyright:  2015 The Regents of the University of California (Regents). All rights reserved.

@license:    Apache

@contact:    ucbjrl@berkeley.edu
@deffield    updated: Updated
'''

from __future__ import print_function
import re
import sys
import os

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.1
__date__ = '2015-07-20'
__updated__ = '2015-07-20'

DEBUG = 1
TESTRUN = 0
PROFILE = 0

testREs = {
           'cdComponent' : re.compile(r""".*make -C (?P<component>\w+) check"""),
           'compile' : re.compile(r""".+sbt\" .*\"run (?P<name>\w+)  --targetDir"""),
           'start' : re.compile(r"""^\[info\] Running (?P<component1>\w+)\.(?P<component2>\w+) (?P<name>\w+) .*--test"""),
           'error' : re.compile(r"""^\[error\] """),
           'success' : re.compile(r"""^\[success\] """),
           'firrtl' : re.compile(r""".+fir2flo.sh (?P<name>\w+)"""),
           'done' : re.compile(r"""^Done!"""),
           'flo' : re.compile(r""".+flo2app.sh (?P<name>\w+)"""),
           'flofin' : re.compile(r"""^GPP DONE"""),
           'test' : re.compile(r"""^STARTING"""),
           'passed' : re.compile(r"""^PASSED"""),
           'failed' : re.compile(r"""^\*\*\* FAILED \*\*\*""")
           }

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def resultsToCSV(path):
    with open(path) as testfile:
        results = {}
        component = ''
        componentName = ''
        for line in testfile.readlines():
            cdcm = testREs['cdComponent'].match(line)
            cm = testREs['compile'].match(line)
            sm = testREs['start'].match(line)
            if cdcm:
                component = cdcm.group('component')
            elif cm:
                componentName = component + '.' + cm.group('name')
                results[componentName] = { 'state' : 'scala', 'scala' : '', 'firrtl' : '', 'flo' : '', 'test' : '' }
            elif sm:
                componentName2 = sm.group('component1') + '.' + sm.group('name')
                if False and componentName2 != componentName:
                    raise CLIError('unexpected state: %s != %s' % (componentName2, componentName))
#                results[componentName]['flo'] = 'passed'
                results[componentName]['state'] = 'test'
            elif componentName != '':
                for re in ['firrtl', 'done', 'flo', 'flofin', 'error', 'success', 'test', 'passed', 'failed']:
                    m = testREs[re].match(line)
                    if m:
                        state = results[componentName]['state']
                        if re == 'test':
                            results[componentName]['state'] = 'test'
                            if results[componentName]['flo'] == '':
                                results[componentName]['flo'] = 'failed'
                        if re == 'flofin':
                            if results[componentName]['flo'] == '':
                                results[componentName]['flo'] = 'passed'
                        elif re == 'passed':
                            results[componentName]['test'] = 'passed'
                            componentName = ''
                        elif re == 'failed':
                            results[componentName]['test'] = 'failed'
                            componentName = ''
                        elif re == 'error':
                            if results[componentName][state] == '':
                                results[componentName][state] = 'failed'
                        elif re == 'success':
                            if results[componentName][state] == '':
                                results[componentName][state] = 'passed'
                        elif re == 'firrtl':
                            if results[componentName]['scala'] == '':
                                results[componentName]['scala'] = 'passed'
                            results[componentName]['state'] = 'firrtl'
                        elif re == 'done':
                            if results[componentName]['firrtl'] == '':
                                results[componentName]['firrtl'] = 'passed'
                            results[componentName]['state'] = 'flo'
                        elif re == 'flo':
                            if results[componentName]['firrtl'] == '':
                                results[componentName]['firrtl'] = 'passed'
                            results[componentName]['state'] = 'flo'
                        break
                else:
                    continue
        print ("Code\tScala\tFIRRTL\tFLO\tTest")       
        for test in sorted(results):
            result = results[test]
            print ("%s\t%s\t%s\t%s\t%s" % (test, result['scala'], result['firrtl'], result['flo'], result['test']))       
    
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
  Copyright 2015 The Regents of the University of California (Regents). All rights reserved.

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
        parser.add_argument(dest="paths", help="paths to folder(s) with source file(s) [default: %(default)s]", metavar="path", nargs='+')

        # Process arguments
        args = parser.parse_args()

        paths = args.paths
        verbose = args.verbose

        if verbose > 0:
            print("Verbose mode on", file=sys.stderr)

        for inpath in paths:
            ### do something with inpath ###
            resultsToCSV(inpath)
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
        profile_filename = 'sbttest.results_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())
