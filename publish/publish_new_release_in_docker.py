#!/usr/bin/env python3
"""publishes a new release, either major or minor"""

import os
from os.path import expandvars
import sys
from argparse import ArgumentParser
import subprocess

def gitConfigGet(value):
    cmd = ["git", "config", "--get", value]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        msg = f"Could not determine git config value for '{value}', please provide one via CLI"
        raise Exception(msg)
    value = proc.stdout.decode().strip()
    return value

def platform():
    if sys.platform == "darwin":
        return "macos"
    elif sys.platform.startswith("linux"):
        return "linux"
    else:
        raise Exception(f"Unsupported platform {sys.platform}")


def platformSpecific(key):
    lookup = {
        "macos": {
            "sshagent": "/run/host-services/ssh-auth.sock"
        },
        "linux": {
            "sshagent": "$SSH_AUTH_SOCK" # TODO may need to do env lookup
        }
    }
    return lookup[platform()][key]


def sshAgent():
    return platformSpecific("sshagent")

def makeParser():
    # TODO expose and propagate options from 'publish_new_release.py'
    parser = ArgumentParser()
    parser.add_argument("-e", "--email", action="store", default=gitConfigGet("user.email"),
                        help="Git config user.email, defaults to 'git config --get user.email'")
    parser.add_argument("-n", "--name", action="store", default=gitConfigGet("user.name"),
                        help="Git config user.name, defaults to 'git config --get user.name'")
    parser.add_argument("--ssh-agent", action="store", default=sshAgent(),
                        help=f"Git config user.name, defaults to '{sshAgent()}'")
    return parser


def main():
    parser = makeParser()
    args = parser.parse_args()
    print(args)

    container_home = "/root"
    host_home = expandvars("$HOME")

    # Step 1 - Build Docker Image
    # TODO actually do this
    # Run from root of the repo
    # docker build -f resources/Dockerfile -t chiselrelease:latest .

    # Step 2 - Run release
    # TODO figure out how to have the Docker container stick around if it fails or go away if it passes
    environment = {
        "PYTHONPATH": "/work/chisel-repo-tools",
        "VERSIONING": "$PYTHONPATH/versioning/versioning.py"
    }
    lines = [
        f"git config --global user.email {args.email}",
        f"git config --global user.name {args.name}",
        f"git config -l",
        "hostname",
        f"git clone git@github.com:chipsalliance/treadle.git"
    ]
    joined = "; ".join(lines)
    script = f"bash -c '{joined}'"
    base_cmd = ["docker", "run", "--rm", "-it"]
    # SSH Agent forwarding
    ssh_agent = ["-v", f"{args.ssh_agent}:/ssh-agent", "-e", "SSH_AUTH_SOCK=/ssh-agent"]
    # Known hosts mapping
    known_hosts = ["-v", f"{host_home}/.ssh/known_hosts:{container_home}/.ssh/known_hosts"]
    cmd =  base_cmd + ssh_agent + known_hosts + [ "chiselrelease:latest", "bash", "-c", joined]
    proc1 = subprocess.run(["echo", "$PATH"], shell=True)
    print(proc1)
    print(cmd)
    proc = subprocess.run(cmd) #, capture_output=True)
    #print(proc.stdout.decode())
    #print(proc.stderr.decode())


if __name__ == "__main__":
    main()
