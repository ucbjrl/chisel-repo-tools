'''
repocontributors.repocon -- extract contributors from GitHib repo stats

repocontributors.repocon is a module that connects to a GitHub repo and extracts contribution information.

@author:     Jim Lawson

@copyright:  2014 UC Berkeley. All rights reserved.

@license:    license

@contact:    ucbjrl@berkeley.edu
@deffield    updated: Updated
'''

import os
import re
import signal
import sys
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from citJenkins.monitorRepos import MonitorRepos

__all__ = []
__version__ = 0.1
__date__ = '2015-07-30'
__updated__ = '2015-07-30'

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

localRepoNames = [ '/Users/jrl/noArc/clients/ucb/git/ucb-bar/chisel:master']
unweightedLogins = set(['Lawson_Jim', 'Mirolo_Sebastien'])
doExit = False
continueOnError = False

homeDir = os.getcwd()

def sigterm(signum, frame):
    global doExit
    print 'repocon: signal %d' % (signum)
    if signum == signal.SIGTERM:
        doExit = True


class areaRE:
    def __init__(self, area, reString):
        self.area = area
        self.reString = reString
        self.re = re.compile(self.reString)

areaREs = [
        areaRE('documentation', r'doc/'),
        areaRE('testing', r'(src/test/)|/(((AdvTester)|(Tester)|(Assert))\.scala)'),
        areaRE('fixpt', r'/((Fixed)|(fixpt))\.scala'),
        areaRE('cpp backend', r'/Cpp\.scala'),
        areaRE('verilog backend', r'/Verilog\.scala'),
        areaRE('library components', r'/ChiselUtil\.scala'),
        areaRE('dot backend', r'/Dot\.scala'),
        areaRE('vcd dumping', r'/Vcd\.scala'),
        areaRE('common backend', r'/Backend\.scala'),
        areaRE('clocks', r'/Clock\.scala'),
        areaRE('FPGA backend', r'/FPGA\.scala'),
        areaRE('Fame backend', r'/FameBackend\.scala'),
        areaRE('SystemC backend', r'/((SCWrapper)|(SysC))\.scala'),
        areaRE('memory', r'/((Mem)|(ROM))\.scala'),
        areaRE('optimization', r'/((PartitionIslands)|(CSE))\.scala'),
        areaRE('aggregates', r'/((Bundle)|(Vec))\.scala'),
        areaRE('infrastructure', r'(Makefile)|(/((Driver)|(ChiselError)|(hcl)|(Version))\.scala)'),
        areaRE('language', r'/((Binding)|(BitPat)|(Bits)|(Bool)|(Complex)|(Data)|(Enum)|(FP)|(Flo)|(IO)|(ImplcitConversions)|(JHFormat)|(Lit)|(Module)|(Node)|(Null)|(Reg)|(UInt)|(Width)|(when))\.scala'),
        areaRE('operators', r'/((Cat)|(Op)|(Insert)|(Extract)|(Log2)|(Lookup)|(Mux))\.scala')
        ]

def areasFromFiles(files):
    areas = []
    if len(files) > 10 and False:
        areas.append('general')
    fileStr = ' '.join(files)
    for areaRE in areaREs:
        if areaRE.re.search(fileStr):
            areas.append(areaRE.area)
    return frozenset(areas)
        
def areasFromChanges(changes):
    areas = set()
    for change in changes:
        areas.update(change['areas'])
    return frozenset(areas)

specialNames = set([
                    'ben-k',
                    'bwrcbcr',
                    'grebe',
                    'jcmartin',
                    'Martoni',
                    'metanext'
                    ])

def ChiselFixName(name):
    if name == 'jackbackrack':
        name = 'Jonathan Bachrach'
    elif name == 'albert-magyar':
        name = 'Albert Magyar'
    elif name == 'U-Ducky-x230t\Ducky' or name == 'Ducky':
        name = 'Richard Lin'
    return name

def doWork(paths, verbose):
#    modName = __name__ + '.doWork'
    
    repos = MonitorRepos(paths)
    if repos is None:
        exit(1)
    
    for (repoName, repoObj) in repos.repoMap.iteritems():
        isRepoLocal = False
        repo = None
        if isRepoLocal:
            repo = repoObj.repo
        else:
            repo = repoObj.remoterepo

        # Although iter_contributors() returns a User object, and iter_pulls() returns a PullRequest containing a User object,
        #  these objects seem rather sparse (the 'name', 'company', and 'email' fields are empty).
        #  We extract the login name from these supposed User objects then fetch the full User object from the repo.
#        contribNames = {}
#        contribNames = [c.login for c in repoObj.remoterepo.iter_contributors()]
#        contribNames = [c.login for c in repo.iter_contributors()]
        contribs = {}
        extUsers = {}
        emailAddresses = {}
        if not isRepoLocal:
            sha = ''
            for pr in repo.pull_requests(state='all'):
                login = pr.user.login
                title = pr.title if pr.title and pr.title != '' else pr.body_text
                files = [f.filename for f in pr.files()]
                if not contribs.has_key(login):
                    contribs[login] = []
                areas = areasFromFiles(files)
                contribs[login].append({ 'sha': sha, 'title': title, 'files': files, 'areas': areas })
#              print '%d, %d\n' % (len(contribs.keys()), len(contribs[login]))

#        for commit in repo.remoterepo.iter_commits():
        for commit in repo.iter_commits() if isRepoLocal else repo.commits():
            sha = ''
            login = ''
            title = ''
            files = []
            try:
                if isRepoLocal:
                    sha = commit.hexsha
                    email = commit.author.email
                    name = ChiselFixName(commit.author.name)
                    # Do we have a user for this email address?
                    if emailAddresses.has_key(email):
                        name = emailAddresses[email]
                    else:
                        emailAddresses[email] = name
                    # 'name' may not be unique, but the same user may have multiple email addresses.
                    (first, sep, last) = name.rpartition(' ')
                    login = last + '_' + first
                    title = commit.summary
                    files = commit.stats.files.keys()
                    if not extUsers.has_key(login):
                        extUsers[login] = {'name': name, 'email': email, 'company': ''}
                else:
                    commit.refresh()
                    # If there isn't an author record, this probably originated outside of github
                    if commit.author is None:
                        login = commit.commit.author[u'email']
                        title = commit.commit.message
                        if not extUsers.has_key(login):
                            extUsers[login] = {'name': commit.commit.author[u'name'], 'email': commit.commit.author[u'email'], 'company': ''}
                    else:
                        login = commit.author.login if commit.author.login and commit.author.login != '' else commit.committer.login
                        title = commit.commit.message
                    sha = commit.sha
                    # Fetch the (normally) missing fields.
                    files = [f[u'filename'] for f in commit.files]

                if not contribs.has_key(login):
                    contribs[login] = []
                areas = areasFromFiles(files)
                contribs[login].append({ 'sha': sha, 'title': title, 'files': files, 'areas': areas })
#              print '%d, %d\n' % (len(contribs.keys()), len(contribs[login]))
                break
            except Exception, e:
                print e

        osep = '\t'
        def weight(x):
            w = 0
            if x not in unweightedLogins:
                w = len(contribs[x])
            return w
                
        def sortContributions(x, y):
            result = 0
            wx = weight(x)
            wy = weight(y)
            if wx != wy:
                result = wy - wx
            else:
                result = cmp(x.lower(), y.lower())
            return result

        for login in sorted(set(contribs.keys()), cmp=sortContributions):
            username = ''
            usercompany = ''
            useremail = ''
            user = None if isRepoLocal else repoObj.gh.user(login)
            if user:
                username = user.name
                usercompany = user.company
                useremail = user.email
            else:
                extuser = extUsers[login]
                username = extuser['name']
                usercompany = extuser['company']
                useremail = extuser['email']
                
            areaSet = set()
            number = 0
            if contribs.has_key(login):
                areaSet = areasFromChanges(contribs[login])
                number = len(contribs[login])
            areas = ', '.join(areaSet)
            info = {'contribs': str(number), 'login': login, 'name': username, 'company': usercompany, 'email': useremail, 'areas': areas}
            fields = [info[k] if info[k] else '' for k in ['contribs', 'login', 'name', 'company', 'email', 'areas']]
            print osep.join(fields)

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
  Copyright 2014 UC Berkeley. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

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
        parser.add_argument(dest="paths", help="paths to folders containing clones of github repositories to be tested [default: %(default)s]",  default=localRepoNames, metavar="path", nargs='*')

        # Process arguments
        args = parser.parse_args()

        paths = args.paths
        verbose = args.verbose

        if verbose > 0:
            print("Verbose mode on")

        # Install the signal handler to catch SIGTERM
        signal.signal(signal.SIGTERM, sigterm)
        doWork(paths, verbose)
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
        profile_filename = 'repocontributors.repocon_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    main()
