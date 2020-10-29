
import subprocess

result = subprocess.run(
    ["grep", "-n", "Tests: succeeded.*failed [1-9]", "../snapshots-3.4/run_tests_test.out"]
)
result = subprocess.run(
    ["grep", "\[error\]", "../snapshots-3.4/run_tests_test.out"]
)
print ("Result: " + str(result.returncode))

