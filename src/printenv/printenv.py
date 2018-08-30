'''
Created on Mar 9, 2016

@author: jrl
'''
import os

if __name__ == '__main__':
    for k in sorted(os.environ.keys()):
        print "%s=%s" % (k, os.environ[k])
