#

import os, sys
import subprocess
import re

from versioning import versioning


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
            print(f"running step {step_number}")
            step_function(*args, **kwargs)
        else:
            print(f"skipping step {step_number}")

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

        versioning_script = 'versioning/versioning.py'

        right_python_path = next(path for path in os.getenv("PYTHONPATH").split(':') if os.path.exists(f"{path}/{versioning_script}"))

        command = f"python {right_python_path}/{versioning_script} verify"
        command_result = subprocess.run(f"{command} >& {self.log_name}", shell=True, capture_output=False)

        if command_result.returncode != 0:
            print(f"{command} failed with error {command_result.returncode}, see {self.log_name} for details")
            exit(1)

        # versioning.main(["verify"])

        self.step_complete()