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
import itertools
from pathlib import Path
from argparse import ArgumentParser, FileType
from argparse import RawDescriptionHelpFormatter
from version.Version import CNVersion
from citSupport.monitorRepos import BaseRepo
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

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
        self.msg = msg
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

class ScalaText:
    commentREs = re.compile(r'(?P<line>//)|(?P<begin>/\*)|(?P<end>\*/)')

    @staticmethod
    def decomment(line: str, inComment: bool) -> (str, bool):
        commentBegin = 0 if inComment else None
        commentEnd = None
        comments = []
        for m in re.finditer(ScalaText.commentREs, line):
            if m.group('line'):
                if not inComment:
                    commentBegin = m.start('line')
                    break
            elif m.group('begin'):
                if not commentBegin:
                    commentBegin = m.start('begin')
                inComment = True
            elif m.group('end'):
                if inComment:
                    commentEnd = m.end('end')
                    comments.append((commentBegin, commentEnd))
                    commentBegin = None
                    commentEnd = None
                    inComment = False

        if commentBegin is not None and commentEnd is None:
            commentEnd = len(line)
            comments.append((commentBegin, commentEnd))
        reversedComments = comments.reverse() if len(comments) > 1 else comments
        for c in reversedComments:
            line = line[:c[0]] + line[c[1]:]
        return((line, inComment))

mapRegex = {
    'begin' : re.compile(r'\bval defaultVersions = Map\('),
#    'entry' : re.compile(r'(?P<prefix>([^"]*"(?P<moduleName>([[:alnum:]_-]+))"\s*->\s*"))' + CNVersion.versionRegex.pattern + '(?P<suffix>(".*))$'),
#    'entry' : re.compile(r'(?P<prefix>([^"]*)")(?P<moduleName>([\w-]+))"\s*->\s*"(?P<version>([\w-]+))(?P<suffix>(".*))$'),
#    'entry' : re.compile(r'(?P<prefix>(\s*"(?P<moduleName>([\w-]+))"\s*->\s*"))(?P<version>([\w-]+))(?P<suffix>(".*))$'),
    'entry' : re.compile(r'(?P<prefix>(\s*"(?P<moduleName>([\w-]+))"\s*->\s*"))(?P<version>(' + CNVersion.versionRegex.pattern + '))(?P<suffix>(".*))$'),
    'end' : re.compile(r'\)')
}

versionFiles = {
    'build.sbt' : {
        'decomment' : ScalaText.decomment,
        'versionTag': r'[^[:alnum:]]version[[:space:]]*:=[[:space:]]*',
        'versionLineRegex' : re.compile(r'^(?P<prefix>.*\bversion\s*:=\s*")(?P<version>(' + CNVersion.versionRegex.pattern + r'))(?P<suffix>".*)$'),
        'moduleNameRegex' : re.compile(r'^\s*name\s*:=\s*"(?P<moduleName>[^"]+)"'),
        'mapBeginRegex' : mapRegex['begin'],
        'mapEntryRegex' : mapRegex['entry'],
        'mapEndRegex' : mapRegex['end']
    },
    'build.sc' : {
        'decomment' : ScalaText.decomment,
        'versionTag': r'[^[:alnum:]]def[[:space:]]+publishVersion[[:space:]]*=[[:space:]]*',
        'versionLineRegex' : re.compile(r'^(?P<prefix>.*\bdef publishVersion\s*=\s*")(?P<version>(' + CNVersion.versionRegex.pattern + r'))(?P<suffix>".*)$'),
        'moduleNameRegex' : re.compile(r'^\s*override\s+def\s+artifactName\s*=\s*"(?P<moduleName>[^"]+)"'),
        'mapBeginRegex' : mapRegex['begin'],
        'mapEntryRegex' : mapRegex['entry'],
        'mapEndRegex' : mapRegex['end']
    }
}

class WorkContext:
    def __init__(self, args: str, versionConfig: dict, path: str, findMinor: bool):
        self.args = args
        self.path = path
        self.repo = BaseRepo(self.path)
        self.versionConfig = versionConfig
        self.versionConfigUpdated = False
        self.files = []
        self.findMinor = findMinor
        self.version = None
        self.moduleVersionMap = None

    def currentMinorVersionFromGitTags(self, major: str, path: str) -> CNVersion:
        vt = None
        proc = subprocess.run(['git', 'tag', '-l'], cwd=path, capture_output=True, check=True, text=True)
        if proc.returncode == 0:
            majorMatch = re.compile(re.escape(major) + r'\.(?P<minor>(\d+))(-|\b)')
            tags = proc.stdout.split('\n')
            candidates = sorted(filter(majorMatch.search, tags), reverse=True)
            for c in candidates:
                vt = CNVersion(aString=c.strip('v'))
                if vt and vt.theInts[2] is not None:
                    break
        return vt

    def currentMinorVersionFromGitChangelog(self, major: str, path: str, baseFileName: str) -> CNVersion:
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

    def getVersions(self) -> dict:
        """
        Determine the version(s) of a module (and sub-modules).
        :return: a dictionary containing module names and versions for any modules found beneath the specified path.
        """
        line = None
        # If there is a build.sbt or build.sc file, we may be able to extract the version using sbt
        dir = Path(self.path)
        self.files = [f for f in dir.glob('**/build.s*') if os.path.basename(f) == 'build.sbt' or os.path.basename(f) == 'build.sc']
        modules = {}
        for f in self.files:
            baseFilename = os.path.basename(f)
            modulePath = os.path.dirname(f)
            (relRoot, moduleDir) = os.path.split(modulePath)
            if moduleDir == 'sbt' and self.path == 'rocket-chip':
                continue
            if not modulePath in modules.keys():
                modules[modulePath] = {}
                modules[modulePath]['paths'] = {}
            filePath = os.path.normpath(f)
            modules[modulePath]['paths'][filePath] = {}
            fileops = versionFiles[baseFilename]
            versionTag = fileops['versionTag']
            versionLineRegex = fileops['versionLineRegex']
            decomment = fileops['decomment']
            moduleRE = fileops['moduleNameRegex']
            myVersion = None
            myModuleName = None
            with open(f, 'r') as input:
                inComment = False
                for l in input:
                    (line, inComment) = decomment(l.rstrip('\n'), inComment)
                    mm = moduleRE.search(line)
                    if mm:
                        myModuleName = mm.group('moduleName')
                        if myVersion:
                            break

                    lm = versionLineRegex.search(line)
                    if lm:
                        versionString = lm.group('version')
                        myVersion = CNVersion(aString=versionString)
                        if myModuleName:
                            break

            modules[modulePath]['paths'][filePath]['version'] = myVersion
            modules[modulePath]['paths'][filePath]['moduleName'] = myModuleName

        return (modules)

    def determineVersion(self, modules: dict) -> dict:
        """
        Determine the version of a module.
        :return: a dictionary containing module names and versions for any modules found beneath the specified path.
        """
        for modulePath, module in modules.items():

            possibleModuleNames = []
            possibleVersions = []
            for filePath, fileVersion in module['paths'].items():
                baseFilename = os.path.basename(filePath)
                modPath = os.path.dirname(filePath)
                (relRoot, moduleDir) = os.path.split(modPath)
                myVersion = fileVersion['version']
                # If we don't have a minor version and we need it, try and deduce it from git tags.
                if myVersion.theInts[2] is None and self.findMinor:
                    deducedVersions = []
                    mismatchedVersions = []
                    major = '.'.join([str(i) for i in myVersion.theInts[CNVersion.MAJOR_SLICE]])
                    if self.repo:
                        vt = self.currentMinorVersionFromGitTags(major, modPath)
                        if vt:
                            deducedVersions.append(CNVersion(aVersion=myVersion, theInts=vt.theInts))
                        vt = self.currentMinorVersionFromGitChangelog(major, modPath, baseFilename)
                        if vt:
                            deducedVersions.append(CNVersion(aVersion=myVersion, theInts=vt.theInts))
                    if len(deducedVersions) > 0:
                        for v in deducedVersions[1:]:
                            if v != deducedVersions[0]:
                                mismatchedVersions.append(v)
                        if len(mismatchedVersions) == 0:
                            myVersion = deducedVersions[0]
                possibleVersions.append(myVersion)

                myModuleName = fileVersion['moduleName']
                if not myModuleName:
                    myModuleName = 'rocketchip' if moduleDir == 'rocket-chip' else moduleDir

                possibleModuleNames.append(myModuleName)

            module['moduleName'] = None
            if len(possibleModuleNames) > 0:
                mismatchedModuleNames = []
                for v in possibleModuleNames[1:]:
                    if v != possibleModuleNames[0]:
                        mismatchedModuleNames.append(v)
                if len(mismatchedModuleNames) == 0:
                    module['moduleName'] = possibleModuleNames[0]

            module['version'] = None
            if len(possibleVersions) > 0:
                mismatchedVersions = []
                for v in possibleVersions[1:]:
                    if v != possibleVersions[0]:
                        mismatchedVersions.append(v)

                if len(mismatchedVersions) == 0:
                    module['version'] = possibleVersions[0]

        return (modules)

    def writeVersion(self, moduleDir: str, module: dict, version: CNVersion):
        """
        Update files containing module versions.
        """
        versionStr = version.releaseVersion() if version.isRelease() else version.snapshotVersion()
        # Update any build.sbt or build.sc file with the specified version.
        for f, fv in module['paths'].items():
            fv['version'] = version
            baseFilename = os.path.basename(f)
            fileops = versionFiles[baseFilename]
            versionLineRegex = fileops['versionLineRegex']
            mapBeginRegex = fileops['mapBeginRegex']
            mapEntryRegex = fileops['mapEntryRegex']
            mapEndRegex = fileops['mapEndRegex']
            decomment = fileops['decomment']
            inputName = str(f)
            outputName = inputName + '.versioning'
            w = Path(outputName)
            update = False
            inComment = False
            inMap = False
            with open(f, 'r') as input, open(w, 'w') as output:
                for l in input:
                    line = l.rstrip('\n')
                    (test, inComment) = decomment(line, inComment)
                    # Do we have a version map in the uncommented line?
                    mm = None
                    if not inMap:
                        mm = mapBeginRegex.match(test)
                        if mm:
                            inMap = True
                    if inMap:
                        mm = mapEntryRegex.search(test)
                        if mm:
                            mm = mapEntryRegex.search(line)
                            if mm:
                                moduleName = mm.group('moduleName')
                                if moduleName not in self.moduleVersionMap:
                                    print("%s not in moduleVersionMap (%s)" % (moduleName, ", ".join(self.moduleVersionMap.keys())))
                                else:
                                    newVersion = self.moduleVersionMap[moduleName]
                                    oldVersion = mm.group('version')
                                    if oldVersion != newVersion:
                                        prefix = mm.group('prefix')
                                        suffix = mm.group('suffix')
                                        line = prefix + newVersion + suffix
                                        update = True
                        mm = mapEndRegex.search(test)
                        if mm:
                            inMap = False

                    # Do we have a valid version setting in the uncommented line?
                    lm = versionLineRegex.match(test)
                    if lm:
                        lm = versionLineRegex.match(line)
                        if lm:
                            oldVersion = CNVersion(aString=lm.group('version'))
                            if oldVersion != version:
                                prefix = lm.group('prefix')
                                suffix = lm.group('suffix')
                                line = prefix + versionStr + suffix
                                update = True
                    print(line, file=output)
            if update and self.args.update:
                os.rename(inputName, inputName + '.bak')
                os.rename(outputName, inputName)
            else:
                os.remove(outputName)
            self.versionConfigUpdated |= update
        if self.versionConfig[moduleDir]['version'] != version:
            self.versionConfig[moduleDir]['version'] = version
            self.versionConfigUpdated = True



def doWork(wc):
    failed = [n for n, m in wc.versionConfig.items() if m['version'] is None]

    if len(failed) > 0:
        raise CLIError("Couldn't determine version for %s" % (', '.join(failed)))

    if wc.args.command == 'verify':
        modules = wc.determineVersion(wc.getVersions())
        for modulePath, module in modules.items():
            mName = module['moduleName']
            if not mName:
                print("Couldn't determine module name for %s" % (modulePath), file=sys.stderr)

            mVersion = module['version']
            if not mVersion:
                print("Couldn't determine module version for %s" % (modulePath), file=sys.stderr)

            if mName and mVersion:
                cModule = {}
                if modulePath not in wc.versionConfig.keys():
                    cModule['moduleName'] = mName
                    cModule['version'] = mVersion
                    cModule['paths'] = module['paths']
                    wc.versionConfig[modulePath] = cModule
                else:
                    cModule = wc.versionConfig[modulePath]
                    if cModule['version'] != mVersion or cModule['moduleName'] != mName:
                        print('verify: %s - %s (%s) != %s (%s)' % (modulePath, cModule['moduleName'],  cModule['version'], mName, mVersion))
                        cModule['moduleName'] = mName
                        cModule['version'] = mVersion
                        cModule['paths'] = module['paths']
                        wc.versionConfigUpdated = True

    else:
        moduleDir = wc.path
        module = wc.versionConfig[moduleDir]
        version = module['version']

        setVersion = None
        action = 'set' if wc.args.update else '(would set)'
        if wc.args.command == 'bump-min':
            setVersion = version.bumpMinor()
        elif wc.args.command == 'bump-maj':
            setVersion = version.bumpMajor()
        elif wc.args.command == 'set':
            if wc.args.release:
                setVersion = CNVersion(aVersion=version, releaseQualifier=wc.args.release)
            elif wc.args.snapshot:
                setVersion = CNVersion(aVersion=version, snapshotQualifier=wc.args.snapshot)
            else:
                setVersion = version
        versionString = setVersion.releaseVersion() if setVersion.isRelease() else setVersion.snapshotVersion()
        print('%s: %s, %s:%s' % (moduleDir, version, action, versionString))
        wc.writeVersion(moduleDir, module, setVersion)

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
    minorMatch = re.compile(r'')
    def hasMinor(versionString: str) -> bool:
        m = CNVersion.versionRegex.match(versionString)
        return True if m and m.group('minor') is not None else False

    global continueOnError
    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('-c', '--config', dest='config', action='store', help='config file containing all module versions', default='version.yml')
        parser.add_argument('-m', '--minor', dest='findMinor', action='store_true', help='determine minor version if it\'s not explicit')
        parser.add_argument('-r', '--release', dest='release', action='store', nargs='?', help='generate release version')
        parser.add_argument('-s', '--snapshot', dest='snapshot', action='store', nargs='?', help='generate snapshot version')
        parser.add_argument('-u', '--update', dest='update', action='store_true', help='Update changed files')
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument(dest='command', choices=['bump-min', 'bump-maj', 'verify', 'set'])
        parser.add_argument(dest='paths', help='paths to search for files to be manipulated (build.s*)', nargs='*')

        # Process arguments
        args = parser.parse_args()

        verbose = args.verbose

        if verbose > 0:
            print("Verbose mode on")

        # Install the signal handler to catch SIGTERM
        signal.signal(signal.SIGTERM, sigterm)

        if args.release and args.snapshot:
            raise CLIError("Can't specify both release and snapshot")

        # Load the version configuration
        configFilename = args.config
        versionConfigs = {}
        configUpdated = False
        if configFilename and os.path.exists(configFilename):
            configInput = open(configFilename, 'r', encoding="utf-8")
            versionConfigs = load(configInput, Loader=Loader)
            configInput.close()

        # Find those modules for which we don't have any information
        needVersions = set(args.paths).difference(set(versionConfigs.keys()))
        findMinor = args.findMinor
        if args.command == 'bump-min' or args.command == 'bump-max':
            if args.release or args.snapshot:
                rOrs = args.release if args.release else args.snapshot
                raise CLIError("%s and %s is ambiguous. Please specify one or the other." % (rOrs, args.command))
            if not args.update:
                print("-u not specified - changes won't be made", file=sys.stderr)
            missingMinors = [md for md, m in versionConfigs.items() if md in args.paths and not m['version'].hasMinor()]
            if len(missingMinors):
                findMinor = True
                needVersions = needVersions.union(set(missingMinors))

        if len(needVersions) > 0:
            prefix = 'Incomplete' if findMinor else 'No'
            print('%s versions for %s: using heuristics' % (prefix, ', '.join(needVersions)))
            for path in needVersions:
                workContext = WorkContext(args, versionConfigs, path, findMinor)
                modules = workContext.determineVersion(workContext.getVersions())
                for modulePath, module in modules.items():
                    mName = module['moduleName']
                    mVersion = module['version']
                    mPaths = module['paths']
                    newModule = {}
                    if modulePath not in versionConfigs.keys():
                        versionConfigs[modulePath] = newModule
                    else:
                        newModule = versionConfigs[modulePath]
                    newModule['moduleName'] = mName
                    newModule['version'] = mVersion
                    newModule['paths'] = mPaths
                    configUpdated = True


        moduleVersionMap = {c['moduleName']:str(c['version']) for md, c in versionConfigs.items() if md in args.paths}
        for path in args.paths:
            workContext = WorkContext(args, versionConfigs, path, findMinor)
            workContext.moduleVersionMap = moduleVersionMap
            doWork(workContext)
            configUpdated |= workContext.versionConfigUpdated

        modules = versionConfigs
        moduleNames = set([m['moduleName'] for md, m in modules.items() if md in args.paths])
        for mName in moduleNames:
            vl = [v['version'] for v in [d for dl in [list(pl.values()) for pl in [m['paths'] for md, m in modules.items() if md in args.paths and m['moduleName'] == mName]] for d in dl]]
            possibleVersions = set(vl)
            if len(possibleVersions) > 1:
                ambiguousModuleDirs = [(md, v['version'], f) for md, m in modules.items() if md in args.paths and m['moduleName'] == mName for f, v in list(m['paths'].items()) if v['version'] in possibleVersions]
                print("Ambigous versions for %s: %s" % (mName, ', '.join([("%s: %s - %s" % (a[0], a[1], a[2])) for a in ambiguousModuleDirs])))

        if args.update and configUpdated:
            outputFilename = configFilename + '.versioning'
            configOutput = open(outputFilename, 'w', encoding="utf-8")
            dump(versionConfigs, configOutput)
            configOutput.close()
            if os.path.exists(configFilename):
                os.rename(configFilename, configFilename + '.bak')
            os.rename(outputFilename, configFilename)
        return 0

    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except CLIError as e:
        sys.stderr.write(program_name + ": " + e.msg + "\n")
        sys.exit(1)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print (''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        if not(DEBUG or TESTRUN):
            indent = len(program_name) * " "
            sys.stderr.write(program_name + ": " + repr(e) + "\n")
            sys.stderr.write(indent + "  for help use --help")
        sys.exit(2)

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
