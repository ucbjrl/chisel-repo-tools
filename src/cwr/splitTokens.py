'''
Created on Sep 18, 2014

@author: jrl
'''
import re

class splitTokens(object):
    '''
    Token splitter - split a string into 'tokens'
    '''


    def __init__(self):
        '''
        '''
        self.tokenRegExString = r"""(\W+)"""
        self.tokenRegEx = re.compile(self.tokenRegExString)

    def tokenize(self, str):
        return self.tokenRegEx.split(str)
