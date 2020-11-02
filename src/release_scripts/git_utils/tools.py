#

import os
import subprocess
import re


def run_this_step(step_function):
    """
    Conditionally runs a step
    """
    def wrapper(*args, **kwargs):
        print(f"arg1 {args[0]}")
        tool_object = args[0]
        step_number = args[1]
        start_step = getattr(tool_object, 'get_start_step')(tool_object)
        stop_step = getattr(tool_object, 'get_stop_step')(tool_object)

        if start_step <= step_number <= stop_step:
            print(f"running step {step_number}")
            print(f"step {step_function(*args, **kwargs)}")
        else:
            print(f"skipping step {step_number}")
        # print(f"step, start, stop {step_number} {start_step} { stop_step}")
        # print(f"object {dir(tool_object)}")
        # print(f"object {getattr(tool_object, 'get_start_step')(tool_object)}")
        # print(f"step {step_function(*args, **kwargs)}")
        # print(step_function)

        exit(1)

    return wrapper


class Tools:
    def __init__(self, task_name):
        self.task_name = task_name
        self.log_name = f"log_{task_name}"
        self.check_release_dir()

        self.white_space = re.compile('\s')

        if not os.path.exists(self.log_name):
            os.mkdir(self.log_name)
        elif not os.path.isdir(self.log_name):
            print(f"Error: {self.log_name} exists but is not a directory")
            exit(1)

        self.start_step, self.stop_step = -1, 1000

    def set_start_step(self, start_step):
        self.start_step = start_step

    def set_stop_step(self, stop_step):
        self.stop_step = stop_step

    def get_start_step(self, start_step):
        return self.start_step

    def get_stop_step(self, stop_step):
        return self.stop_step

    def check_step(self, step_number: int) -> bool:
        step_number >= self.start_step and step_number <= self.stop_step

    def check_release_dir(self):
        """Looks to see that target is a clone of chisel-release"""
        command_result = subprocess.run(["git", "remote", "-v"], text=True, capture_output=True)
        if command_result.returncode != 0:
            print("You appear to be in the wrong directory")
            print(f"{os.getcwd()} does not appear to be a git repo")
            exit(1)

    @run_this_step
    def checkout_branch(self, step_number, branch_name: str) -> None:
        """checkout specified branch"""

        function_name = "checkout_branch"
        log_name = self.step_log_name(step_number, function_name)

        command_result = subprocess.run(
            f"git checkout {branch_name} &> {log_name}",
            shell=True,
            capture_output=False)
        if command_result.returncode != 0:
            print(f"git checkout {branch_name} failed, see {log_name} for details")
            exit(1)

        print(f"Now on branch {branch_name}")

    def run_pull(self, step_number: int) -> None:
        """runs git pull"""

        function_name = "run_pull"
        log_name = self.step_log_name(step_number, function_name)

        command_result = subprocess.run(
            f"git pull &> {log_name}",
            shell=True,
            capture_output=False)
        if command_result.returncode != 0:
            print(f"git pull failed, see {log_name} for details")
            exit(1)

        print(f"git pull complete")

    def run_submodule_update_recursive(self, step_number):
        """run git submodule update --init --recursive"""

        function_name = "run_submodule_update_recursive"
        log_name = self.step_log_name(step_number, function_name)

        command_result = subprocess.run(
            f"git submodule update --init --recursive &> {log_name}",
            shell=True,
            capture_output=False)

        if command_result.returncode != 0:
            print(f"git submodule update recursive failed, see {log_name} for details")
            exit(1)

        print(f"git submodule update --init --recursive complete")

    def run_make_pull(self, step_number):
        """run make pull"""

        function_name = "make_pull"
        log_name = self.step_log_name(step_number, function_name)

        command_result = subprocess.run(
            f"make pull &> {log_name}",
            shell=True,
            capture_output=False)
        if command_result.returncode != 0:
            print(f"make pull failed, see {log_name} for details")
            exit(1)

        print(f"make pull complete")

    def run_make_clean_install(self, step_number):
        """run make clean install"""

        function_name = "run_make_clean_install"
        log_name = self.step_log_name(step_number, function_name)

        command_result = subprocess.run(
            f"make -j8 -f Makefile clean pull &> {log_name}",
            shell=True,
            capture_output=False)

        if command_result.returncode != 0:
            print(f"make -j8 -f Makefile clean install failed, see {log_name} for details")
            exit(1)

        print(f"make clean install complete")

    def run_make_test(self, step_number):
        """run make test"""

        function_name = "run_make_test"
        log_name = self.step_log_name(step_number, function_name)

        command_result = subprocess.run(
            f"make -j8 -f Makefile test &> {log_name}",
            shell=True,
            capture_output=False)

        if command_result.returncode != 0:
            print(f"make -j8 -f Makefile clean install failed, see {log_name} for details")
            exit(1)

        print(f"make test complete")

    def step_log_name(self, step_number: int, step_name) -> str:
        """create the correct name for a log file"""

        log_file_name = f"{self.log_name}/step_{step_number:03d}_{step_name}"
        if self.white_space.search(log_file_name):
            print(f"Error: {step_number} {step_name} generated log name '{log_file_name} contains white space")
            exit(1)

        return log_file_name
