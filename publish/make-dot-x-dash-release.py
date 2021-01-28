"""
After a new major release has been made you can use this script to create the
`Z.Y.x` and `Z.Y-release` branches.
TODO: This is still a WIP, needs more docs and error checks
"""
import os
import subprocess

import yaml

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from version.Version import CNVersion


def load_versions_file(config_file_name: str) -> dict:
    config_input = open(config_file_name, 'r', encoding="utf-8")
    version_configs = yaml.load(config_input, Loader=Loader)
    config_input.close()
    internal_configs = {}
    for modulePath, versions in version_configs['versions'].items():
        internal_configs[modulePath] = {}
        internal_configs[modulePath]['packageName'] = versions['packageName']
        internal_configs[modulePath]['version'] = CNVersion(aString=versions['version'])

    return internal_configs


versions_from_yaml = load_versions_file("../../masters/version.yml")

repo_versions = {}
for key in versions_from_yaml.keys():
    repo_versions[key] = versions_from_yaml[key]['version']

for repo, version in repo_versions.items():
    print(f"repo: {repo} -> {version}")

save_dir = os.getcwd()

for a, b in repo_versions.items():
    dot_x = f"{b}.x"
    dash_release = f"{b}-release"
    print(f"{a} -> ({dot_x}, {dash_release})")
    os.chdir(f"../masters/{a}")
    result = subprocess.run(["git branch --show-current"], shell=True, capture_output=True)
    branch = result.stdout.decode("utf-8")[:-1]
    print(f"current branch {branch}")
    if result.returncode == 0 and branch == "master":
        print(f"creating branch {dot_x}")
        subprocess.run(f"git checkout -b {dot_x}", shell=True)
        subprocess.run(f"git push -u origin {dot_x}", shell=True)

        print(f"creating branch {dash_release}")
        subprocess.run(f"git checkout -b {dash_release}", shell=True)
        subprocess.run(f"git push -u origin {dash_release}", shell=True)
    else:
        print(f"branch {dot_x} already exists")

    os.chdir(save_dir)
