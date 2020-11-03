#

import os
import subprocess
import re


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

        # print(f"step, start, stop {step_number} {start_step} { stop_step}")
        # print(f"object {dir(tool_object)}")
        # print(f"object {getattr(tool_object, 'get_start_step')(tool_object)}")
        # print(f"step {step_function(*args, **kwargs)}")
        # print(step_function)

    return wrapper


class Tools:
    def __init__(self, task_name):
        self.task_name = task_name
        self.log_dir = f"log_{task_name}"
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
        # used to find things like Makefiles
        self.execution_dir = ""

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
            f"git commit -m '{commit_message}' &> {self.log_name}",
            shell=True,
            capture_output=False)
        if command_result.returncode != 0:
            print(f"git commit failed, see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def git_add(self, step_number: int) -> None:
        """runs git pull"""

        command_result = subprocess.run(
            f"git add &> {self.log_name}",
            shell=True,
            capture_output=False)
        if command_result.returncode != 0:
            print(f"git add failed, see {self.log_name} for details")
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
            f"make pull &> {self.log_name}",
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
            f"make -j8 -f Makefile clean install &> {self.log_name}",
            shell=True,
            capture_output=False)

        if command_result.returncode != 0:
            print(
                f"make -j8 -f Makefile clean install failed ({command_result.returncode}), see {self.log_name} for details")
            exit(1)

        self.step_complete()

    @command_step
    def run_make_test(self, step_number):
        """run make test"""

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
                print(f"make -j8 -f Makefile clean install failed, see {self.log_name} for details")

            return has_errors

        command_result = subprocess.run(
            f"make -j8 -f Makefile test &> {self.log_name}",
            shell=True,
            capture_output=False)

        if command_result.returncode != 0:
            print(f"make -j8 -f Makefile clean install failed, see {self.log_name} for details")
            show_errors()
            exit(1)

        if show_errors():
            exit(1)

        self.step_complete()
