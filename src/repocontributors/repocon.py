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
from citSupport.monitorRepos import MonitorRepos

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

specialName = re.compile(r'''.*Ducky.*''')

ghlmap = (
          ('jcmartin', 'James Martin'),
          ('ben-k', 'Ben Keller'),
          ('da-steve101', 'Stephen Tridgell'),
          ('Martoni', 'Fabien Marteau')
       )
def chiselFixLogin(name):
    if name == 'jackbackrack':
        name = 'Jonathan Bachrach'
    elif name == 'albert-magyar':
        name = 'Albert Magyar'
    elif name == 'U-Ducky-x230t\Ducky' or name == 'Ducky':
        name = 'Richard Lin'
    return name

emailAddresses = {}
def canonicalName(name, login, email):
    ''' Return the canonical name from the supplied arguments.
    '''
    result = ''
    if name:
        result = chiselFixLogin(name)
    else:
        testl = ''
        if login:
            testl = chiselFixLogin(login)
        # Do we have an email address?
        teste = ''
        if email and emailAddresses.has_key(email):
            teste = emailAddresses[email]
        # Did we generate a name from the login name?
        if testl and testl != login:
            result = testl
        elif teste:
            result = teste
        elif testl:
            result = testl
        else:
            result = email
    if email:
        emailAddresses[email] = result
    return result

# We manage duplicates by storing user info in three dictionaries keyed on the name, email, and login.
# If there are no duplicates, each dictionary will have a single entry for each key.
users = { 'id': {}, 'login': {}, 'name': {}, 'email': {} }
def addUserInfo(uId, login, name, email, company):
    modName = __name__ + 'addUserInfo'
    thisKey = { 'id': uId, 'login': login, 'name': name, 'email': email }
    for metaId in users.keys():
        try:
            thisId = thisKey[metaId]
            if thisId:
                # Assume we'll want to add this record
                doAdd = True
                if not users[metaId].has_key(thisId):
                    users[metaId][thisId] = []
                else:
                    # We already have some records. Is this one of them?
                    for val in users[metaId][thisId]:
                        if val['id'] == uId:
                            doAdd = False
                            break
                if doAdd:
                    users[metaId][thisId].append({'id': uId, 'login': login, 'name': name, 'email': email, 'company': company })
        except Exception, e:
            print '%s in %s' % (e, modName)
            raise(e)

def getUserInfo(uid):
    modName = __name__ + 'getUserInfo'
    try:
        u = users['id'][uid][0]
        return u

    except Exception, e:
        return None

def uniqueUsers():
    modName = __name__ + 'uniqueUsers'
    idMap = {}
    for metaId in users.keys():
        for key, vals in users[metaId].iteritems():
            try:
                if vals and len(vals) > 1:
                    # We've found a duplicate.
                    # key is the common field.
                    if metaId in set(['login', 'id']):
                        # This shouldn't happen. 'id' and 'login' should be unique
                        raise CLIError('%s duplicate - "%s"' % (metaId, key))
                    elif metaId in set(['email', 'name']):

                        def sortVals(x, y):
                            ''' Choose the best id for this user.
                                Our preference is the one with the longest name, or the shortest email address.'''
                            result = 0
                            xnameWeight = len(x['name']) if x['name'] else 0
                            ynameWeight = len(y['name']) if y['name'] else 0
                            if xnameWeight > ynameWeight:
                                result = -1
                            elif xnameWeight == ynameWeight:
                                xemailWeight = len(x['email']) if x['email'] else sys.maxsize
                                yemailWeight = len(y['email']) if y['email'] else sys.maxsize
                                if xemailWeight < yemailWeight:
                                    return -1
                                elif xemailWeight > yemailWeight:
                                    return 1
                            else:
                                result = 1
                            return result

                        pref = sorted(vals, cmp=sortVals)[0]
                        for val in vals:
                            if val['id'] != pref['id']:
                                old = val['id']
                                new = pref['id']
                                # Do we already have this mapping
                                if idMap.has_key(old):
                                    if idMap[old] != new:
                                        raise CLIError('inconsistent duplicate map (%s, %s) for %d' % (idMap[old], new, old))
                                else:
                                    idMap[old] = new
            except Exception, e:
                print '%s in %s' % (e, modName)
                raise(e)
    return idMap
                    

def doWork(paths, verbose):
    modName = __name__ + '.doWork'
    
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
        if not isRepoLocal:
            sha = ''
            for pr in repo.pull_requests(state='closed'):
                contribId = pr.user.login
                title = pr.title if pr.title and pr.title != '' else pr.body_text
                files = [f.filename for f in pr.files()]
                if not contribs.has_key(contribId):
                    contribs[contribId] = []
                areas = areasFromFiles(files)
                contribs[contribId].append({ 'sha': sha, 'title': title, 'files': files, 'areas': areas })
#              print '%d, %d\n' % (len(contribs.keys()), len(contribs[contribId]))
                break
#        for commit in repo.remoterepo.iter_commits():
        for commit in repo.iter_commits() if isRepoLocal else repo.commits():
            sha = ''
            contribId = ''
            title = ''
            files = []
            aName = ''
            name = ''
            email = ''
            contribId = None
            login = None
            try:
                if isRepoLocal:
                    sha = commit.hexsha
                    email = commit.author.email
                    aName = commit.author.name
                    # 'name' may not be unique, but the same user may have multiple email addresses.
                    if (not (specialName.match(aName) or specialName.match(email)) and False):
                        continue
                    (first, sep, last) = aName.rpartition(' ')
                    contribId = last + '_' + first
                    title = commit.summary
                    files = commit.stats.files.keys()
                else:
                    commit.refresh()
                    # If there isn't an author record, this probably originated outside of github
                    if commit.author is None:
                        email = commit.commit.author[u'email']
                        aName = commit.commit.author[u'name']
                        contribId = aName if aName else email
                        title = commit.commit.message
                    else:
                        # We'll pick up name and email after we've collected all the logins.
                        login = commit.author.login
                        contribId = login
                        title = commit.commit.message
                    sha = commit.sha
                    # Fetch the (normally) missing fields.
                    files = [f[u'filename'] for f in commit.files]

                name = canonicalName(aName, login, email)
                if not contribs.has_key(contribId):
                    contribs[contribId] = []
                    if aName or email:
                        addUserInfo(contribId, login, name, email, '')
                areas = areasFromFiles(files)
                contribs[contribId].append({ 'sha': sha, 'title': title, 'files': files, 'areas': areas })
#                print '%d, %d, %d\n' % (len(contribs.keys()), len(contribs[contribId]), len(users['id'].keys()))
#                if len(contribs.keys()) > 5:
#                    break
            except Exception, e:
                print '%s in %s' % (e, modName)
                raise(e)

        # Go through the contributions and get the author info for non-local repos.
        if not isRepoLocal:
            for contribId in contribs.keys():
                # Do we have a GitHub login for this Id?
                login = contribId
                ui = getUserInfo(contribId)
                if ui:
                    login = ui['login']
                if login:
                    user = repoObj.gh.user(login)
                    if user:
                        name = canonicalName(user.name, contribId, user.email)
                        addUserInfo(contribId, contribId, name, user.email, user.company)
                    else:
                        print 'no GutHub user info for - "%s"' % (contribId)
                    
        # Go through the contributions and try to coalesce those from the same author.
        for oldId, newId in uniqueUsers().iteritems():
            contribs[newId] += contribs[oldId]
            del contribs[oldId]

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

        for contribId in sorted(set(contribs.keys()), cmp=sortContributions):
            ui = getUserInfo(contribId)
            if ui:
                number = len(contribs[contribId])
                areaSet = areasFromChanges(contribs[contribId])
                areas = ', '.join(areaSet)
                info = {'contribs': str(number), 'contribId': ui['id'], 'name': ui['name'], 'company': ui['company'], 'email': ui['email'], 'areas': areas}
                fields = [info[k] if info[k] else '' for k in ['contribs', 'contribId', 'name', 'company', 'email', 'areas']]
                print osep.join(fields)
            else:
                print 'Could not find "%s" in userInfo' % (contribId)

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
