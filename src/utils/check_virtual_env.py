
import sys
import os

if sys.prefix == sys.base_prefix:
    print ('You do not appear to be in the correct virtual environment')
    print ('Consult doc/release')
    exit(1)

versioning = os.getenv("PYTHONPATH")
if versioning == None or len(versioning) == 0:
    print ("PYTHONPATH env var must point to an existing directory, probably the src dir from chisel-repo-tools")
    exit(1)

if not os.path.exists(versioning):
    print ("Env var $PYTHONPATH=" + versioning + "does not point to an existing file, probably the src dir from chisel-repo-tools")
    exit(1)

versioning = os.getenv("VERSIONING")
if versioning == None or len(versioning) == 0:
    print ("VERSIONING env var must point to an existing file, probably named versioning.py")
    exit(1)

if not os.path.exists(versioning):
    print ("Env var $VERSIONING=" + versioning + "does not point to an existing file, probabluy named versioning.py")
    exit(1)

