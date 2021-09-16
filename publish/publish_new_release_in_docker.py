#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Example use: ./publish/publish_new_release_in_docker.py -- -m 3.4 -bt minor"""
# Notes
# * This requires the ability to run docker WITHOUT sudo. This seems to be the
#   default on MacOS but required additional steps on Ubuntu.
#   See https://docs.docker.com/engine/install/linux-postinstall/
# * This also has only been tested when using keychain to manage the ssh agent
#   (on both MacOS and Ubuntu)

# Useful commands
# # Build the docker file
# > docker build -f resources/Dockerfile -t ucbbar/chisel-release:latest .
#
# # Connect to a running container
# > docker exec -it <container> bash
#
# # Stop a container
# > docker stop <container>
#
# # Delete all stopped containers
# > docker container prune

import os
from os.path import expandvars
import sys
from argparse import ArgumentParser
import subprocess
import shutil
from pathlib import Path
import publish_new_release as pnr
import re


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
            "sshagent": os.environ["SSH_AUTH_SOCK"]
        }
    }
    return lookup[platform()][key]


def sshAgent():
    return platformSpecific("sshagent")


def prettifyCommand(cmd):
    def escape(l):
        return l.replace("\"", "\\\"")
    def quote(l):
        if " " in l or "\"" in l :
            return "\"" + escape(l) + "\""
        else:
            return l
    quoted = [quote(x) for x in cmd]
    return " ".join(quoted)


def flatten(l):
    return [item for sublist in l for item in sublist]


def formatValues(d):
    return { k: v.format(**d) for k, v in d.items() }


def subenvars(cmd):
    def subvar(arg):
        # Find $VARIABLE not preceded by \
        m = re.match(r'.*(?<!\\)\$(\w+).*', arg)
        if m:
            var = m.group(1)
            resolved = os.environ.get(var)
            if resolved is None:
                raise Exception(f"Environment variable '{var}' must be defined!")
            subbed = re.sub(f"\${var}", resolved, arg)
            return subbed
        else:
            return arg
    return [subvar(arg) for arg in cmd]


def makeParser():
    # TODO expose and propagate options from 'publish_new_release.py'
    parser = ArgumentParser()
    parser.add_argument("-e", "--email", action="store", default=gitConfigGet("user.email"),
                        help="Git config user.email, defaults to 'git config --get user.email'")
    parser.add_argument("-n", "--name", action="store", default=gitConfigGet("user.name"),
                        help="Git config user.name, defaults to 'git config --get user.name'")
    parser.add_argument("--ssh-agent", action="store", default=sshAgent(),
                        help=f"Local SSH agent to mount in container, defaults to '{sshAgent()}'")
    parser.add_argument("args", type=str, nargs="+",
                        help="Arguments for publish_new_release.py that will be run in Docker container")
    return parser


def find_container(image_name):
    cmd = ["docker", "ps", "--filter", f"ancestor={image_name}", "--format", "{{.Names}}"]
    proc = subprocess.run(cmd, capture_output=True)
    lines = proc.stdout.decode().strip().split("\n")

    res = [x for x in lines if x != ""]

    if len(res) > 1:
        raise SystemExit(f"There needs to be 1 or fewer {image_name} containers, got {res}!")
    if len(res) == 0:
        return None
    else:
        return res[0]


def launch_container(args, image_name):
    container_home = "/root"
    host_home = expandvars("$HOME")

    # SSH Agent forwarding
    ssh_agent = ["-v", f"{args.ssh_agent}:/ssh-agent", "-e", "SSH_AUTH_SOCK=/ssh-agent"]
    # Known hosts mapping
    known_hosts = ["-v", f"{host_home}/.ssh/known_hosts:{container_home}/.ssh/known_hosts"]

    base_cmd = ["docker", "run", "-t", "-d"]
    cmd =  base_cmd + ssh_agent + known_hosts + [image_name]

    print(f"Running '{prettifyCommand(cmd)}'")
    proc = subprocess.run(cmd, capture_output=True)

    return proc.stdout.decode().strip()


def run_commands(container, environment, lines):
    joined = "; ".join(lines)
    script = f"bash -c '{joined}'"
    base_cmd = ["docker", "exec"]
    env = flatten([["-e", f"{name}={value}"] for name, value in environment.items()])

    fake_cmd = base_cmd + env + [container, "bash", "-c", joined]
    print(f"Running '{prettifyCommand(fake_cmd)}'")

    # It's important to not print the subbed environment variables which have secrets
    secret_cmd = base_cmd + subenvars(env) + [container, "bash", "-c", joined]

    proc = subprocess.run(secret_cmd)


def main():
    parser = makeParser()
    args = parser.parse_args()

    # Check forwarded args
    forwarded_args = args.args
    pnr_parser = pnr.make_parser()
    pnr_parser.parse_args(forwarded_args)

    image_name = "ucbbar/chisel-release:latest"

    # Step 1 - Setup Docker container

    # Find or launch container
    container = find_container(image_name)

    if container is None:
        print("No container running, starting...")
        launch_container(args, image_name)
        # Launch container does return the id, but find_container gives the prettier name
        container = find_container(image_name)
        # Some setup commands
        cmds = [
            "git clone git@github.com:ucb-bar/chisel-release.git",
            f"git config --global user.email {args.email}",
            f"git config --global user.name {args.name}",
            # This is needed for pushing tags at the end of release during test_new_release.py
            'git config --global url."git@github.com:".insteadOf "https://github.com/"',
        ]
        run_commands(container, {}, cmds)

    print(f"Running in container {container}")

    # Step 2 - Run release

    # Environment needed to run publish commands
    # NOTE: Anything with an environment variable will be subbed in subprocess.run
    #       but will NOT be echoed to the screen, this is mainly for secrets
    environment = formatValues({
        "PYTHONPATH": "/work/chisel-repo-tools/src",
        "VERSIONING": "{PYTHONPATH}/versioning/versioning.py",
        "PGP_SECRET": "$PGP_SECRET",
        "PGP_PASSPHRASE": "$PGP_PASSPHRASE",
        "SONATYPE_USERNAME": "$SONATYPE_USERNAME",
        "SONATYPE_PASSWORD": "$SONATYPE_PASSWORD",
    })

    splat_args = " ".join(forwarded_args)

    lines = [
        "cd chisel-release",
        "echo $PGP_SECRET | base64 --decode | gpg --batch --import",
        f"python3 -u ../chisel-repo-tools/publish/publish_new_release.py {splat_args}",
    ]

    run_commands(container, environment, lines)

    # Step 3 - Finalize Release on Sonatype
    # See docs/sonatype_finalize_release.md
    # TODO integrate into publish_new_release

    # Step 4 - Tag Release
    # Run publish/tag_new_release.py
    # TODO integrate into publish_new_release


if __name__ == "__main__":
    main()
