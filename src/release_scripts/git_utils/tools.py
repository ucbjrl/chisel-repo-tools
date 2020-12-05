#

import os, sys
import subprocess
import re

from datetime import datetime


def command_step(step_function):
    """
    This is a decorator function that performs several functions
    - checks that the command associated with the step_number should be run
    - get the name of the function being run and use is as the step name
    - generator a log file name for this command based on the function name
    - if in list mode just show the step number and name and do not run the command
    """

    def wrapper(*args, **kwargs):
        tool_object = args[0]

        step_number = args[1]
        getattr(tool_object, 'set_current_step')(step_number)

        start_step = getattr(tool_object, 'get_start_step')()
        stop_step = getattr(tool_object, 'get_stop_step')()

        function_name = str(step_function).split(" ")[1].split('.')[1]
        getattr(tool_object, 'set_current_function_name')(function_name)

        log_dir = getattr(tool_object, 'get_log_dir')()
        log_name = f"{log_dir}/step_{step_number:03d}_{function_name}"
        getattr(tool_object, 'set_current_log_name')(log_name)
        list_only = getattr(tool_object, 'get_list_only')()
        # print(f"function name {function_name}")

        if list_only:
            print(f"step {step_number:3d} {function_name}")
        elif start_step <= step_number <= stop_step:
            print(f"running step {step_number} {function_name}")
            step_function(*args, **kwargs)
        else:
            print(f"skipping step {step_number} {function_name}")

    return wrapper


class Tools:
    """
    This is the toolbox for the tools necessary to run release scripts
    A release script is basically a list of the tasks that need to be done in
    a specific order. Each step (command) must specify a step number, that can
    be used to re-run script starting at a particular number and/or ending at one.
    The command_step decorator handles this and a number of additional common
    operations such as extracting the commands string name from the method name.
    """

    def __init__(self, task_name, release_dir):
        self.task_name = task_name
        self.log_dir = f"log_{task_name}"

        if release_dir is None or release_dir == "":
            print(f"Release dir cannot be empty, try --help to see options")
            exit(1)

        self.release_dir = release_dir
        self.execution_dir = os.getcwd()
        os.chdir(release_dir)
        self.check_release_dir()

        self.white_space = re.compile('\s')

        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)
        elif not os.path.isdir(self.log_dir):
            print(f"Error: {self.log_dir} exists but is not a directory")
            exit(1)

        stamps_dir = f"{release_dir}/stamps"
        if not os.path.exists(stamps_dir):
            os.mkdir(stamps_dir)
        elif not os.path.isdir(stamps_dir):
            print(f"Error: {stamps_dir} exists but is not a directory, needed for some logging operations")
            exit(1)

        # currently executing step
        self.current_step = -1
        # externally set start and stop step, default is do all steps
        self.start_step, self.stop_step = -1, 1000
        # current function name
        self.current_function = ""
        # log file of current_command
        self.current_log_file = ""
        # set this to True to only list the commands in the script
        self.list_only = False
        # default Makefile name, used for clean, pull, install, test
        self.default_makefile = f"{self.execution_dir}/resources/Makefile"

    @staticmethod
    def get_versioning_command(sub_command: str) -> str:
        python_path = os.getenv("PYTHONPATH")
        versioning_script = 'versioning/versioning.py'

        try:
            right_python_path = next(
                path for path in python_path.split(':') if os.path.exists(f"{path}/{versioning_script}"))
        except StopIteration:
            print(f"Unable to find a path to {versioning_script} in PYTHONPATH={python_path}")
            exit(1)

        args = ""
        if sub_command == "verify":
            args = "verify"
        elif sub_command == "ds":
            now = datetime.now()
            day_stamp = now.strftime("%Y%m%d")
            args = f'-s {day_stamp} write'
        elif sub_command == "date-stamped-clear":
            args = f'-s "" write'
        elif sub_command == "major":
            args = "bump-maj"
        elif sub_command == "minor":
            args = "bump-min"
        elif sub_command == "rc-clear":
            args = '-r "" write'
        elif sub_command.startswith("rc"):
            pattern = re.compile('rc(\d+)')
            if not pattern.match(sub_command):
                print("Error: bad bump-type, release candidate must be of the form RC<candidate-number>")
                exit(1)
            args = sub_command
        else:
            print("Error: bad bump-type, release candidate must be of major, minor, rc<n>, rc-clear, ds, ds<YYYMMDD>, ds-clear")
            exit(1)

        return f"python {right_python_path}/{versioning_script} {args}"

    def set_execution_dir(self, execution_dir: str):
        self.execution_dir = execution_dir

    def set_current_step(self, current_step: int):
        self.current_step = current_step

    def set_start_step(self, start_step):
        self.start_step = start_step

    def set_stop_step(self, stop_step):
        self.stop_step = stop_step

    def get_start_step(self):
        return self.start_step

    def get_stop_step(self):
        return self.stop_step

    def get_current_function_name(self):
        return self.current_function_name

    def set_current_function_name(self, function_name):
        self.current_function_name = function_name

    def get_log_dir(self):
        return self.log_dir

    def set_current_log_name(self, new_log_name):
        self.log_name = new_log_name

    def get_list_only(self) -> bool:
        return self.list_only

    def set_list_only(self, value: bool):
        self.list_only = value

    def step_complete(self, msg: str = ""):
        print(f"step {self.current_step} - {self.current_function_name} is complete. {msg}")

    def check_step(self, step_number: int) -> bool:
        step_number >= self.start_step and step_number <= self.stop_step

    def check_release_dir(self):
        """Looks to see that target is a clone of chisel-release"""
        command_result = subprocess.run(["git", "remote", "-v"], text=True, capture_output=True)
        if command_result.returncode != 0:
            print("You appear to be in the wrong directory")
            print(f"{os.getcwd()} does not appear to be a git repo")
            exit(1)

    @command_step
    def checkout_branch(self, step_number, branch_name: str) -> None:
        """checkout specified branch"""

        command_result = subprocess.run(
            f"git checkout {branch_name} &> {self.log_name}",
            shell=True,
            capture_output=False)
        if command_result.returncode != 0:
            print(f"git checkout {branch_name} failed, see {self.log_name} for details")
            exit(1)

        self.step_complete(f"Now on branch {branch_name}")

    @command_step
    def git_pull(self, step_number: int) -> None:
        """runs git pull"""

        command_result = subprocess.run(
            f"git pull &> {self.log_name}",
            shell=True,
            capture_output=False)
        if command_result.returncode != 0:
            print(f"git pull failed, see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def git_push(self, step_number: int) -> None:
        """runs git push"""

        command_result = subprocess.run(
            f"git push &> {self.log_name}",
            shell=True,
            capture_output=False)
        if command_result.returncode != 0:
            print(f"git push failed, see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def git_commit(self, step_number: int, commit_message: str) -> None:
        """runs git commit"""

        command_result = subprocess.run(
            f"git diff-index --quiet HEAD || git commit -m '{commit_message}' &> {self.log_name}",
            shell=True,
            capture_output=False)
        if command_result.returncode != 0:
            print(f"git commit failed, see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def git_add_dash_u(self, step_number: int) -> None:
        """runs git pull"""

        command_result = subprocess.run(
            f"git add -u &> {self.log_name}",
            shell=True,
            capture_output=False)
        if command_result.returncode != 0:
            print(f"git add -u failed, see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def run_submodule_update_recursive(self, step_number):
        """run git submodule update --init --recursive"""

        command_result = subprocess.run(
            f"git submodule update --init --recursive &> {self.log_name}",
            shell=True,
            capture_output=False)

        if command_result.returncode != 0:
            print(f"git submodule update recursive failed, see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def run_make_pull(self, step_number):
        """run make pull"""

        command_result = subprocess.run(
            f"make -f {self.default_makefile} pull &> {self.log_name}",
            shell=True,
            capture_output=False)
        if command_result.returncode != 0:
            print(f"make pull failed, see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def git_merge_masters_into_dot_x(self, step_number):
        """git merge masters into dot x"""
        command = f"""
            git submodule foreach '
                if git diff --cached --quiet; then git merge --no-ff --no-commit master;
                fi
            '  &> {self.log_name}
        """
        command_result = subprocess.run(
            command,
            shell=True,
            capture_output=False)
        if command_result.returncode != 0:
            print(f"make pull failed, see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def run_make_clean_install(self, step_number):
        """run make clean install"""

        command_result = subprocess.run(
            f"make -j8 -f {self.default_makefile} clean install &> {self.log_name}",
            shell=True,
            capture_output=False)

        if command_result.returncode != 0:
            print(
                f"make -j8 -f {self.default_makefile} clean install failed ({command_result.returncode}), see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def run_make_test(self, step_number):
        """run make test"""

        def is_external_program_present(command: str):
            command_result = subprocess.run(f"{command} >> {self.log_name} 2>&1", shell=True, capture_output=False)
            if command_result.returncode != 0:
                just_command = command.split(' ')[0]
                print(f"Required: {just_command} failed, is it installed?, see {self.log_name} for details")
                exit(1)

        def show_errors() -> bool:
            check_result = subprocess.run(
                f"""grep '\\[error\\]' {self.log_name}""",
                shell=True,
                text=True,
                capture_output=True,
            )

            error_lines = check_result.stdout.splitlines()
            has_errors = len(error_lines) > 0
            if has_errors:
                print(f"Errors ({len(error_lines)} found during {self.current_function_name}")
                for line in error_lines:
                    print(line)
                print(f"make -j8 -f {self.default_makefile} clean install failed, see {self.log_name} for details")

            return has_errors

        is_external_program_present(f"verilator -version")
        is_external_program_present(f"yosys -V")
        is_external_program_present(f"z3 --version")

        command_result = subprocess.run(
            f"make -j8 -f {self.default_makefile} test >> {self.log_name} 2>&1",
            shell=True,
            capture_output=False)

        if command_result.returncode != 0:
            print(f"make -j8 -f {self.default_makefile} clean install failed, see {self.log_name} for details")
            show_errors()
            exit(1)

        if show_errors():
            exit(1)

        self.step_complete()

    @command_step
    def verify_merge(self, step_number):
        """verify merge"""

        command = Tools.get_versioning_command("verify")
        command_result = subprocess.run(f"{command} >& {self.log_name}", shell=True, capture_output=False)

        if command_result.returncode != 0:
            print(f"{command} failed with error {command_result.returncode}, see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def bump_release(self, step_number, bump_type: str):
        """bump release versions of submodules"""

        command = Tools.get_versioning_command(bump_type)
        command_result = subprocess.run(f"{command} >& {self.log_name}", shell=True, capture_output=False)

        if command_result.returncode != 0:
            print(f"{command} failed with error {command_result.returncode}, see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def check_version_updates(self, step_number):
        """check that updating the version seems to be ok"""
        command = f"git diff --submodule=diff"
        command_result = subprocess.run(f"{command} >& {self.log_name}", shell=True, text=True, capture_output=False)

        if command_result.returncode != 0:
            print(f"{command} failed with error {command_result.returncode}, see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def add_and_commit_submodules(self, step_number):
        """add and commit all submodules"""
        command = f"""git submodule foreach 'git add -u && git commit -m "Bump version strings." '"""

        command_result = subprocess.run(f"{command}", shell=True, text=True, capture_output=True)

        if command_result.returncode != 0:
            print(f"{command} failed with error {command_result.returncode}, see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def merge_dot_x_branches_into_release_branches(self, step_number):
        """merges commits from .x branches into -release branches"""
        command = f"""
        git submodule foreach '
            if [ "$name" != "rocket-chip" ] && git diff --quiet --cached ; then
                 rbranch=$(git config -f $toplevel/.gitmodules submodule.$name.branch);
                 xbranch=$(echo $rbranch | sed -e 's/-release/.x/');
                 git merge --no-ff --no-commit $xbranch;
            fi'
        """

        command_result = subprocess.run(f"{command}", shell=True, text=True, capture_output=False)

        if command_result.returncode != 0:
            print(f"{command} failed with error {command_result.returncode}, see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def check_dot_x_merge_status(self, step_number):
        """look for any obvious error from merge_dot_x_branches_into_release_branches step"""
        command = f"git status -b uno --ignore-submodules=untracked"

        command_result = subprocess.run(f"{command}", shell=True, text=True, capture_output=False)

        if command_result.returncode != 0:
            print(f"{command} failed with error {command_result.returncode}, see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def commit_each_submodule(self, step_number):
        """commit each submodule"""
        command = f"""
            git submodule foreach '
                if git diff --cached --quiet ; then echo skipping ; else
                    git commit --no-edit
                fi
            '
        """

        command_result = subprocess.run(f"{command}", shell=True, text=True, capture_output=False)

        if command_result.returncode != 0:
            print(f"{command} failed with error {command_result.returncode}, see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def push_submodules(self, step_number):
        """push each submodule"""
        command = f"""git submodule foreach 'git push'"""

        command_result = subprocess.run(f"{command}", shell=True, text=True, capture_output=False)

        if command_result.returncode != 0:
            print(f"{command} failed with error {command_result.returncode}, see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def publish_signed(self, step_number):
        """publish signed"""
        command = f"make -f {self.default_makefile} +publishSigned &> {self.log_name}"

        command_result = subprocess.run(f"{command}", shell=True, text=True, capture_output=False)

        if command_result.returncode != 0:
            print(f"{command} failed with error {command_result.returncode}, see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def comment(self, step_number, message: str):
        """comment"""

        print(message)

        self.step_complete()

    @command_step
    def tag_submodules(self, step_number, is_dry_run: bool):
        """tag submodules"""

        subcommand = "echo" if is_dry_run else "eval"
        command = f"""
             git submodule foreach '
                 rbranch=$(git config -f $toplevel/.gitmodules submodule.$name.branch);
                 xbranch=$(echo $rbranch | sed -e "s/-release/.x/");
                 {subcommand} git tag $(../genTag.sh $xbranch)
             '
        """

        command_result = subprocess.run(f"{command} &> {self.log_name}", shell=True, text=True, capture_output=False)
        if command_result.returncode != 0:
            print(f"{command} failed with error {command_result.returncode}, see {self.log_name} for details")
            exit(1)

        if not is_dry_run:
            command = f"""git submodule foreach 'git describe'"""
            command_result = subprocess.run(f"{command} >> {self.log_name} 2>&1", shell=True, text=True,
                                            capture_output=False)

            if command_result.returncode != 0:
                print(f"{command} failed with error {command_result.returncode}, see {self.log_name} for details")
                exit(1)

            command = f"""git submodule foreach 'git push origin $(git describe)'"""
            command_result = subprocess.run(f"{command} >> {self.log_name} 2>&1", shell=True, text=True,
                                            capture_output=False)

            if command_result.returncode != 0:
                print(f"{command} failed with error {command_result.returncode}, see {self.log_name} for details")
                exit(1)

        self.step_complete()

    @command_step
    def tag_top_level(self, step_number, is_dry_run: bool, release_version: str):
        """tag top level"""

        subcommand = "echo" if is_dry_run else "eval"
        command = f"{subcommand} git tag $(./genTag.sh {release_version} v{release_version})"
        command_result = subprocess.run(f"{command} &> {self.log_name}", shell=True, text=True, capture_output=False)
        if command_result.returncode != 0:
            print(f"{command} failed with error {command_result.returncode}, see {self.log_name} for details")
            exit(1)

        if not is_dry_run:
            command = f"git describe"
            command_result = subprocess.run(f"{command} >> {self.log_name} 2>&1", shell=True, text=True,
                                            capture_output=False)
            if command_result.returncode != 0:
                print(f"{command} failed with error {command_result.returncode}, see {self.log_name} for details")
                exit(1)

            command = f"git push origin $(git describe)"
            command_result = subprocess.run(f"{command} >> {self.log_name} 2>&1", shell=True, text=True,
                                            capture_output=False)
            if command_result.returncode != 0:
                print(f"{command} failed with error {command_result.returncode}, see {self.log_name} for details")
                exit(1)

        self.step_complete()
