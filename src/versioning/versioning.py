'''
versioning.versioning -- module to support version manipulation.

@author:     Jim Lawson

@copyright:  2019 UC Berkeley. All rights reserved.

@license:    BSD-3-Clause

@contact:    ucbjrl@berkeley.edu
@deffield    updated: Updated
'''

import copy
import os
import re
import signal
import subprocess
import sys
import traceback
import yaml
from pathlib import Path, PurePath
from argparse import ArgumentParser, FileType
from argparse import RawDescriptionHelpFormatter
from functools import reduce

from version.Version import CNVersion
from citSupport.monitorRepos import BaseRepo
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
    'begin' : re.compile(r'\bval defaultVersions\s*=\s*(Map|Seq)\('),
    'entry' : re.compile(r'(?P<prefix>(.*"(?P<packageName>([\w-]+))"\s*->\s*"))(?P<version>(' + CNVersion.versionRegex.pattern + '))(?P<suffix>(".*))$'),
    'end' : re.compile(r'\)')
}

versionFiles = {
    'build.sbt' : {
        'decomment' : ScalaText.decomment,
        'versionTag': r'[^[:alnum:]]version[[:space:]]*:=[[:space:]]*',
        'versionLineRegex' : re.compile(r'^(?P<prefix>.*\bversion\s*:=\s*")(?P<version>(' + CNVersion.versionRegex.pattern + r'))(?P<suffix>".*)$'),
        'packageNameRegex' : re.compile(r'^\s*name\s*:=\s*"(?P<packageName>[^"]+)"'),
        'mapBeginRegex' : mapRegex['begin'],
        'mapEntryRegex' : mapRegex['entry'],
        'mapEndRegex' : mapRegex['end']
    },
    'build.sc' : {
        'decomment' : ScalaText.decomment,
        'versionTag': r'[^[:alnum:]]def[[:space:]]+publishVersion[[:space:]]*=[[:space:]]*',
        'versionLineRegex' : re.compile(r'^(?P<prefix>.*\bdef publishVersion\s*=\s*")(?P<version>(' + CNVersion.versionRegex.pattern + r'))(?P<suffix>".*)$'),
        'packageNameRegex' : re.compile(r'^\s*override\s+def\s+artifactName\s*=\s*"(?P<packageName>[^"]+)"'),
        'mapBeginRegex' : mapRegex['begin'],
        'mapEntryRegex' : mapRegex['entry'],
        'mapEndRegex' : mapRegex['end']
    }
}

commands = {
    'read' : {
        'description' : 'read build files and create/update version config cache',
        'prereqs' : ['paths', 'versions'],
        'writeConfig' : True,
        'writeFiles' : False
    },
    'add' : {
        'description' : 'add/update a module to the version config cache',
        'prereqs' : None,
        'writeConfig' : True,
        'writeFiles' : False
    },
    'remove' : {
        'description' : 'remove a module from the version config cache',
        'prereqs' : None,
        'writeConfig' : True,
        'writeFiles' : False
    },
    'write' : {
        'description' : 'update build files from the version config cache',
        'prereqs' : ['paths', 'versions'],
        'writeConfig' : False,
        'writeFiles' : True
    },
    'verify' : {
        'description' : 'read build files and verify they conform to the version config cache',
        'prereqs' : ['versions'],
        'writeConfig' : False,
        'writeFiles' : False
    },
    'bump-maj' : {
        'description' : 'update the major version number for the specified module in the version config cache and build files',
        'prereqs' : ['paths', 'versions'],
        'writeConfig' : True,
        'writeFiles' : True
    },
    'bump-min' : {
        'description' : 'update the minor version number for the specified module in the version config cache and build files',
        'prereqs' : ['minors', 'paths', 'versions'],
        'writeConfig' : True,
        'writeFiles' : True
    },
    'dependency-order' : {
        'description' : 'generate dependency information (build order) from the dependency maps in the build files',
        'prereqs' : ['maps'],
        'writeConfig' : False,
        'writeFiles' : False
    },
    'dependency-array' : {
        'description' : 'generate dependency information (bash associative array) from the dependency maps in the build files',
        'prereqs' : ['maps'],
        'writeConfig' : False,
        'writeFiles' : False
    },
    'dependency-cicache' : {
        'description' : 'generate dependency information (CircleCI cache keys) from the dependency maps in the build files',
        'prereqs' : ['maps'],
        'writeConfig' : False,
        'writeFiles' : False
    },
    'help' : {
        'description' : 'provide help text',
        'prereqs' : None,
        'writeConfig' : False,
        'writeFiles' : False
    }
}
def moduleIsAuthoritative(moduleDir: str) -> bool:
    return len(moduleDir.split(os.path.sep)) == 1

class PackageVersion:
    def __init__(self, name: str, version: CNVersion, map: dict):
        self.name = name
        self.version = version
        self.map = map

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
        self.recurse = True
        self.dryRun = args.dryRun

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

    # Read lines of a file looking for package and version information.
    # If provided with an output file and PackageVersion, copy the file updating the PackageVersion
    def analyzeFileLines(self, fileops, input, updatePackageVersion: PackageVersion = None, output = None) -> PackageVersion:
        versionLineRegex = fileops['versionLineRegex']
        mapBeginRegex = fileops['mapBeginRegex']
        mapEntryRegex = fileops['mapEntryRegex']
        mapEndRegex = fileops['mapEndRegex']
        decomment = fileops['decomment']
        packageNameRegex = fileops['packageNameRegex']
        myVersion = None
        myPackageName = None
        update = False
        inComment = False
        inMap = False
        gotInfo = { 'name' : False, 'version' : False, 'map' : False}
        quitOnAllFound = True if output is None else False
        myPackageVersionMap = {}
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
                        packageName = mm.group('packageName')
                        packageVersion = mm.group('version')
                        myPackageVersionMap[packageName] = packageVersion
                        if updatePackageVersion:
                            if packageName not in updatePackageVersion.map:
                                print("%s not in updatePackageVersion.map (%s)" % (packageName, ", ".join(self.updatePackageVersion.map.keys())))
                            else:
                                newVersion = self.moduleVersionMap[packageName]
                                if packageVersion != newVersion:
                                    prefix = mm.group('prefix')
                                    suffix = mm.group('suffix')
                                    line = prefix + newVersion + suffix
                                    update = True
                mm = mapEndRegex.search(test)
                if mm:
                    inMap = False
                    gotInfo['map'] = True
            else:
                pm = packageNameRegex.search(test)
                if pm:
                    myPackageName = pm.group('packageName')
                    gotInfo['name'] = True

                # Do we have a valid version setting in the uncommented line?
                lm = versionLineRegex.match(test)
                if lm:
                    lm = versionLineRegex.match(line)
                    if lm:
                        myVersion = CNVersion(aString=lm.group('version'))
                        gotInfo['version'] = True
                        if updatePackageVersion and myVersion != updatePackageVersion.version:
                            versionStr = str(updatePackageVersion.version)
                            prefix = lm.group('prefix')
                            suffix = lm.group('suffix')
                            line = prefix + versionStr + suffix
                            update = True
            if quitOnAllFound and reduce(lambda x, y: x and y, gotInfo.values()):
                break
            if output:
                print(line, file=output)
        return (PackageVersion(myPackageName, myVersion, myPackageVersionMap), update)

    def getVersions(self) -> dict:
        """
        Determine the version(s) of a module (and possibly sub-modules).
        :return: a dictionary containing module names and versions for any modules found beneath the specified path.
        """
        # If there is a build.sbt or build.sc file, we may be able to extract the version using sbt
        dir = Path(self.path)
        dirPrefix = '**/' if self.recurse else ''
        self.files = [f for f in dir.glob(dirPrefix + 'build.s*') if os.path.basename(f) == 'build.sbt' or os.path.basename(f) == 'build.sc']
        modules = {}
        for f in self.files:
            baseFilename = os.path.basename(f)
            modulePath = os.path.dirname(f)
            (relRoot, moduleDir) = os.path.split(modulePath)
            dirComponents = PurePath(relRoot).parts
            if moduleDir == 'sbt' and 'rocket-chip' in dirComponents:
                continue
            if not modulePath in modules.keys():
                modules[modulePath] = {}
                modules[modulePath]['paths'] = {}
            filePath = os.path.normpath(f)
            modules[modulePath]['paths'][filePath] = {}
            fileops = versionFiles[baseFilename]
            myPackageVersion = None
            with open(f, 'r') as input:
                (myPackageVersion, dummy) = self.analyzeFileLines(fileops, input)
            modules[modulePath]['paths'][filePath]['version'] = myPackageVersion.version
            modules[modulePath]['paths'][filePath]['packageName'] = myPackageVersion.name
            modules[modulePath]['paths'][filePath]['map'] = myPackageVersion.map

        return (modules)

    def determineVersion(self, modules: dict) -> dict:
        """
        Determine the version of a module.
        :return: a dictionary containing module names and versions for any modules found beneath the specified path.
        """
        packageKeys = ['packageName', 'version', 'map']
        for modulePath, module in modules.items():

            possibilities = {}
            for key in packageKeys:
                possibilities[key] = []
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
                possibilities['version'].append(myVersion)

                myPackageName = fileVersion['packageName']
                if not myPackageName:
                    myPackageName = 'rocketchip' if moduleDir == 'rocket-chip' else moduleDir

                possibilities['packageName'].append(myPackageName)
                possibilities['map'].append(fileVersion['map'])

            mismatched = {}
            for key in packageKeys:
                module[key] = None
                if len(possibilities[key]) > 0:
                    mismatched[key] = []
                    for v in possibilities[key][1:]:
                        if v != possibilities[key][0]:
                            mismatched[key].append(v)
                    if len(mismatched[key]) == 0:
                        module[key] = possibilities[key][0]

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
            inputName = str(f)
            outputName = inputName + '.versioning'
            w = Path(outputName)
            update = False
            packageName = module['packageName']
            myPackageVersion = None
            with open(f, 'r') as input, open(w, 'w') as output:
                updatePackageVersion = PackageVersion(packageName, version, self.moduleVersionMap)
                (myPackageVersion, update) = self.analyzeFileLines(fileops, input, updatePackageVersion, output)
            if update and not self.dryRun:
                os.rename(inputName, inputName + '.bak')
                os.rename(outputName, inputName)
            else:
                os.remove(outputName)
            self.versionConfigUpdated |= update

    def determineDependencies(self) -> dict:
        dependencies = {}
        dependencies['order'] = []
        dependencies['module'] = {}
        moduleDependencies = {md: m for md, m in self.versionConfig.items() if moduleIsAuthoritative(md)}
        packageToModuleMap = {m['packageName']: md for md, m in moduleDependencies.items()}
        # Record the immediate dependencies
        for mdir, module in moduleDependencies.items():
            dependencies['module'][mdir] = set([packageToModuleMap[p] for p in module['map'].keys()])
        modules = list(moduleDependencies.keys())
        makingProgress = True
        while len(modules) and makingProgress:
            d = []
            updateModuleDependencies = copy.deepcopy(moduleDependencies)
            for mdir, module in moduleDependencies.items():
                if len(module['map']) == 0:
                    d.append(mdir)
                    del updateModuleDependencies[mdir]
                    modules.remove(mdir)
                    packageName = module['packageName']
                    for dependencyMap in [m['map'] for m in updateModuleDependencies.values()]:
                        if packageName in dependencyMap.keys():
                            del dependencyMap[packageName]
            moduleDependencies = updateModuleDependencies
            if len(d) > 0:
                dependencies['order'].append(d)
            else:
                makingProgress = False
        if not makingProgress:
            raise CLIError("Couldn't determine dependencies for %s" % (", ".join(modules)))
        # Now walk the dependency list in build order to solve the transitive dependencies
        for mdir in [dd for d in dependencies['order'] for dd in d]:
            dependSets = [dependencies['module'][s] for s in dependencies['module'][mdir]]
            dependencies['module'][mdir] = dependencies['module'][mdir].union(*dependSets)

        return dependencies



def doWork(wc: dict, authoritativeModules: dict) -> int:
    failed = [n for n, m in wc.versionConfig.items() if m['version'] is None]
    if len(failed) > 0:
        raise CLIError("Couldn't determine version for %s" % (', '.join(failed)))

    result = 0
    action = '(would set)' if wc.dryRun else 'set'

    moduleDirs = list(wc.versionConfig.keys())
    if wc.args.command == 'verify':
        modules = wc.determineVersion(wc.getVersions())

        for modulePath, module in modules.items():
            mName = module['packageName']
            if not mName:
                print("Couldn't determine module name for %s" % (modulePath), file=sys.stderr)
                result = 1

            mVersion = module['version']
            if not mVersion:
                print("Couldn't determine module version for %s" % (modulePath), file=sys.stderr)
                result = 1

            if mName and mVersion:
                cModule = {}
                if modulePath not in moduleDirs:
                    print('verify: %s isn\'t in version cache' % (modulePath), file=sys.stderr)
                else:
                    cModule = wc.versionConfig[modulePath]
                    if cModule['version'] != mVersion or cModule['packageName'] != mName:
                        print('verify: %s - %s (%s) != %s (%s)' % (modulePath, cModule['packageName'],  cModule['version'], mName, mVersion), file=sys.stderr)
                        result = 1

    elif wc.args.command == 'add':
        modules = wc.determineVersion(wc.getVersions())

        for modulePath, module in modules.items():
            mName = module['packageName']
            if not mName:
                print("Couldn't determine module name for %s" % (modulePath), file=sys.stderr)
                result = 1

            mVersion = module['version']
            if not mVersion:
                print("Couldn't determine module version for %s" % (modulePath), file=sys.stderr)
                result = 1

            if mName and mVersion:
                localUpdate = False
                cModule = {}
                if modulePath in moduleDirs:
                    print('verify: %s already in version cache - treating as update' % (modulePath), file=sys.stderr)
                    cModule = wc.versionConfig[modulePath]
                    if cModule['version'] != mVersion or cModule['packageName'] != mName:
                        cModule['version'] = mVersion
                        cModule['packageName'] = mName
                        localUpdate = True
                else:
                    cModule['version'] = mVersion
                    cModule['packageName'] = mName
                    wc.versionConfig[modulePath] = cModule
                    localUpdate = True
                if localUpdate:
                    print('verify - add: %s %s %s:%s' % (modulePath, action, mName, mVersion))
                    wc.versionConfigUpdated = True
    else:
        moduleDir = wc.path
        module = wc.versionConfig[moduleDir]
        setVersion = module['version']
        versionString = setVersion.releaseVersion() if setVersion.isRelease() else setVersion.snapshotVersion()
        print('%s: %s:%s' % (moduleDir, action, versionString))
        if wc.versionConfig[moduleDir]['version'] != setVersion:
            wc.versionConfig[moduleDir]['version'] = setVersion
            wc.versionConfigUpdated = True
        wc.writeVersion(moduleDir, module, setVersion)
    return result

def loadVersionConfigs(configFilename: str) -> dict:
    configInput = open(configFilename, 'r', encoding="utf-8")
    versionConfigs = yaml.load(configInput, Loader=Loader)
    configInput.close()
    internalConfigs = {}
    for modulePath, versions in versionConfigs['versions'].items():
        internalConfigs[modulePath] = {}
        internalConfigs[modulePath]['packageName'] = versions['packageName']
        internalConfigs[modulePath]['version'] = CNVersion(aString=versions['version'])

    return internalConfigs

def dumpVersionConfigs(configFilename: str, versionConfigs: dict):
    d = {}
    for packageDir, versions in versionConfigs.items():
        v = {}
        v['packageName'] = versions['packageName']
        v['version'] = str(versions['version'])
        d[packageDir] = v
    externalRepresentation = {}
    externalRepresentation['versions'] = d
    outputFilename = configFilename + '.versioning'
    configOutput = open(outputFilename, 'w', encoding="utf-8")
    yaml.dump(externalRepresentation, configOutput)
    configOutput.close()
    if os.path.exists(configFilename):
        os.rename(configFilename, configFilename + '.bak')
    os.rename(outputFilename, configFilename)

def main(argv=None) -> int: # IGNORE:C0111
    '''Command line options.'''

    exitCode = 0
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
        maxCommandLength = max([len(c) for c in commands.keys()])
        commandDescriptions = '\n' + '\n'.join(['%s%s: %s' % (c, ' '*(maxCommandLength - len(c)), i['description']) for c, i in commands.items()])
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter, epilog=commandDescriptions)
        parser.add_argument('-R', '--recursive', dest='recursive', action='store_true', help='look for version info in any sub-directories')
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('-c', '--config', dest='config', action='store', help='config file containing all module versions', default='version.yml')
        parser.add_argument('-m', '--minor', dest='findMinor', action='store_true', help='determine minor version if it\'s not explicit')
        parser.add_argument('-n', '--dry-run', dest='dryRun', action='store_true', help='don\'t actually modify anything')
        parser.add_argument('-r', '--release', dest='release', action='store', help='generate release version')
        parser.add_argument('-s', '--snapshot', dest='snapshot', action='store', help='generate snapshot version')
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument(dest='command', choices=commands.keys())
        parser.add_argument(dest='paths', help='paths to search for files to be manipulated (build.s*)', nargs='*')

        # Process arguments
        args = parser.parse_args()

        verbose = args.verbose

        if verbose > 0:
            print("Verbose mode on")

        # Install the signal handler to catch SIGTERM
        signal.signal(signal.SIGTERM, sigterm)

        if args.release is not None and args.snapshot is not None:
            raise CLIError("Can't specify both release (-r) and snapshot (-s)")

        if args.command == 'help':
            parser.print_help()
            sys.exit(2)

        # Load the version configuration
        configFilename = args.config
        versionConfigs = {}
        configUpdated = False
        if configFilename and os.path.exists(configFilename):
            versionConfigs = loadVersionConfigs(configFilename)

        modulePaths = []
        if '.' in args.paths and len(args.paths) > 1:
            print('A "." path causes others to be ignored: (%s)' % (", ".join([p for p in args.paths if p != "."])), file=sys.stderr)
            modulePaths = ['.']
        else:
            modulePaths = args.paths if len(args.paths) > 0 else versionConfigs.keys()

        # Find those modules for which we don't have any version information (currently unlikely)
        needVersions = set([vk for vk, vi in versionConfigs.items() if 'version' not in vi or vi['version'] is None])
        findMinor = args.findMinor
        missing = {}
        for key in ['minors', 'paths', 'versions', 'maps']:
            missing[key] = None
        commandDesc = commands[args.command]

        # Does this command update the config file, at least in principle?
        writeConfig = commandDesc['writeConfig'] or args.release is not None or args.snapshot is not None
        if args.dryRun:
            print("-n specified - changes won't be persistent", file=sys.stderr)

        # Do we need minor version numbers?
        if commandDesc['prereqs']:
            if 'minors' in commandDesc['prereqs'] or args.release is not None:
                missing['minors'] = [md for md, m in versionConfigs.items() if md in modulePaths and not m['version'].hasMinor()]
                if len(missing['minors']):
                    findMinor = True
            if 'maps' in commandDesc['prereqs']:
                missing['maps'] = [md for md, m in versionConfigs.items() if md in modulePaths and not 'map' in m]
            if 'paths' in commandDesc['prereqs']:
                missing['paths'] = modulePaths
            if 'versions' in commandDesc['prereqs']:
                missing['versions'] = needVersions

        needVersions = needVersions.union(*[set(m) for m in missing.values() if (m and len(m) > 0)])

        updatedVersions = {}
        if len(needVersions) > 0:
            prefix = 'Incomplete' if missing['minors'] or missing['paths'] else 'No'
            missingPieces = ', '.join([key for key, values in missing.items() if values])
            suffixes = []
            if missing['versions'] or missing['paths']:
                suffixes.append('reading build files')
            if missing['minors']:
                suffixes.append('using heuristics')
            suffix = ','.join(suffixes)
            print('%s %s for %s: %s' % (prefix, missingPieces, ', '.join(needVersions), suffix), file=sys.stderr)
            for path in needVersions:
                workContext = WorkContext(args, versionConfigs, path, findMinor)
                modules = workContext.determineVersion(workContext.getVersions())
                for modulePath, module in modules.items():
                    newModule = versionConfigs[modulePath]
                    # We update paths and map since these aren't saved in the versions cache.
                    newModule['paths'] = module['paths']
                    newModule['map'] = module['map']
                    # Keep the freshly determined version distinct.
                    updatedVersions[modulePath] = module['version']


        moduleDirs = set(modulePaths).union(versionConfigs.keys())
        authoritativeModules = {m['packageName']: m for md, m in versionConfigs.items() if moduleIsAuthoritative(md)}

        # Are we going to update the version information (in the version cache and the build files)?
        if writeConfig and commandDesc['writeFiles']:
            for moduleDir in modulePaths:
                version = updatedVersions[moduleDir]

                setVersion = None
                if args.release is not None:
                    setVersion = CNVersion(aVersion=version, releaseQualifier=args.release)
                elif args.snapshot is not None:
                    setVersion = CNVersion(aVersion=version, snapshotQualifier=args.snapshot)
                else:
                    setVersion = version
                action = 'set' if not args.dryRun else '(would set)'
                if args.command == 'bump-min':
                    setVersion = setVersion.bumpMinor()
                elif args.command == 'bump-maj':
                    setVersion = setVersion.bumpMajor()
                elif args.command == 'set':
                    pass
                # Do we have a version to update?
                oldVersion = versionConfigs[moduleDir]['version']
                if oldVersion != setVersion:
                    versionString = setVersion.releaseVersion() if setVersion.isRelease() else setVersion.snapshotVersion()
                    print('%s: %s, %s:%s' % (moduleDir, oldVersion, action, versionString))
                    versionConfigs[moduleDir]['version'] = setVersion
                    configUpdated = True

        moduleVersionMap = {c['packageName']:str(c['version']) for md, c in versionConfigs.items() if moduleIsAuthoritative(md)}
        if args.command == 'dependency-order' or args.command == 'dependency-array' or args.command == 'dependency-cicache':
            workContext = WorkContext(args, versionConfigs, '.', findMinor)
            workContext.moduleVersionMap = moduleVersionMap
            dependencies = workContext.determineDependencies()
            moduleDirs = [dd for d in dependencies['order'] for dd in d]
            if args.command == 'dependency-order':
                print(" ".join(moduleDirs))
            elif args.command == 'dependency-array':
                for md, d in dependencies['module'].items():
                    print("%s \"%s\"" % (md, " ".join(d)))
            elif args.command == 'dependency-cicache':
                prefix = "v1-dep"
                sep = "--"
                moduleDirsReversed = moduleDirs.copy()
                moduleDirsReversed.reverse()
                # Generate a set of lists (well, tuples so they have constant hashes) of cache key combinations.
                moduleCacheKeys = {}
                for md in moduleDirs:
                    d = dependencies['module'][md]
                    moduleCacheKeys[md] = set(tuple(d)).union(*[moduleCacheKeys[dd] for dd in d])
                for md, d in dependencies['module'].items():
                    modsubs = [dmd for dmd in moduleDirsReversed if dmd in d]
                    modsubkeys = [("%s%s{{ checksum \"%s.sbtcksm\" }}" % (dmd, sep, dmd)) for dmd in modsubs]
                    print("%s%s%s%s{{ checksum \"%s.sbtcksum\" }}%s%s" % (prefix, sep, md, sep, md, sep, sep.join(modsubkeys)))
                    for i in range(len(modsubkeys)):
                        print("%s%s%s" % (prefix, sep, sep.join(modsubkeys[i:])))
            else:
                print('Unrecognized dependency command: %s' % (args.command), file=sys.stderr)
                exitCode = 2

        else:
            for path in modulePaths:
                workContext = WorkContext(args, versionConfigs, path, findMinor)
                workContext.moduleVersionMap = moduleVersionMap
                result = doWork(workContext, authoritativeModules)
                if result == 0:
                    configUpdated |= workContext.versionConfigUpdated
                exitCode = max(exitCode, result)

            # Do we have paths as a prerequisite?
            # If so, check for consistency
            if commandDesc['prereqs'] and 'paths' in commandDesc['prereqs']:
                modules = versionConfigs
                moduleNames = set([m['packageName'] for md, m in modules.items() if md in modulePaths])
                for mName in moduleNames:
                    vl = [v['version'] for v in [d for dl in [list(pl.values()) for pl in [m['paths'] for md, m in modules.items() if md in modulePaths and m['packageName'] == mName]] for d in dl]]
                    possibleVersions = set(vl)
                    if len(possibleVersions) > 1:
                        ambiguousModuleDirs = [(md, v['version'], f) for md, m in modules.items() if md in modulePaths and m['packageName'] == mName for f, v in list(m['paths'].items()) if v['version'] in possibleVersions]
                        print("Ambigous versions for %s: %s" % (mName, ', '.join([("%s: %s - %s" % (a[0], a[1], a[2])) for a in ambiguousModuleDirs])))

            if not args.dryRun and configUpdated:
                dumpVersionConfigs(configFilename, versionConfigs)
        return exitCode

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
    exitCode = main()
    sys.exit(exitCode)
