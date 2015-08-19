'''
Created on Nov 5, 2014

@author: jrl
'''
import os
import re
import stat
import sys

__all__ = []
__version__ = 0.1
__date__ = '2014-11-05'
__updated__ = '2014-11-05'

DEBUG = 1
TESTRUN = 0
PROFILE = 0


class Line2GroupError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg, lineNo = None, lineString = None):
        super(Line2GroupError).__init__(type(self))
        self.msg = "E: %s" % msg
        self.lineNo = lineNo
        self.lineString = lineString
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

class Line2Group:
    def __init__(self):
        self.lineRegex = re.compile(r"""(?P<issue>(#\d+)?) ?(?P<text>.*)$""")
        self.template = '''  <tr>
    <td>\g<issue></td>
    <td>\g<text></td>
  </tr>
'''
    def l2g(self, line):
        mg = self.lineRegex.match(line)
        if mg is None:
            raise Line2GroupError('line doesn\'t match regex - "%s"' % (line))
        text = mg.expand(self.template)
        return text
    
    def test(self):
        lines = ['no issue', '#1 issue 1.']
        for line in lines:
            self.l2g(line)

def main(argv=None):
    '''Command line options.'''
    from argparse import ArgumentParser, RawDescriptionHelpFormatter, FileType

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
        parser.add_argument(dest="file", help="file to convert",  action='store', default=sys.stdin, type=FileType('r'))

        # Process arguments
        args = parser.parse_args()

        verbose = args.verbose
        if verbose > 0:
            print("Verbose mode on")

        l2g = Line2Group()
        for line in args.file:
            print l2g.l2g(line)
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
    
                
if __name__ == '__main__':
    main()
