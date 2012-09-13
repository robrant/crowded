'''
Created on Sep 6, 2012

@author: brantinghamr
'''
import unittest
import os
import sys
import json
#============================================================================================
# TO ENSURE ALL OF THE FILES CAN SEE ONE ANOTHER.

# Get the directory in which this was executed (current working dir)
cwd = os.getcwd()
wsDir = os.path.dirname(cwd)

# Find out whats in this directory recursively
for root, subFolders, files in os.walk(wsDir):
    # Loop the folders listed in this directory
    for folder in subFolders:
        directory = os.path.join(root, folder)
        if directory.find('.git') == -1:
            if directory not in sys.path:
                sys.path.append(directory)

#============================================================================================
import crowdedWorker
from baseUtils import getConfigParameters

class Test(unittest.TestCase):


    def testGetTopTags(self):
        ''' Checks that we're getting the right tags'''
        
        inTags = {'tinker':1,
                  'tailor':100,
                  'soldier':20,
                  'sailor':40,
                  'richman':90,
                  'poorman':92,
                  'beggarman':93,
                  'thief':24}
             
        outTags = crowdedWorker.filterTagsByPercentCount(inTags, 'spy')
        self.assertEquals(outTags, ['tailor(100)', 'beggarman(93)', 'poorman(92)', 'richman(90)'])
        
    
    def testGetTopTagsReal(self):
        ''' Checks that we're getting the right tags'''
        
        f = open('./testResourceAssociatedTags.json', 'r')
        inTags = json.loads(f.read())
             
        outTags = crowdedWorker.filterTagsByCount(inTags, 'PROTest', numberTopTags=3)
        self.assertEquals(outTags, [u'hongkong(47)', u'\u958b\u5b78\u53cd\u6d17\u8166(36)', u'hkig(34)'])
    
    def testPopUselessTags(self):
        ''' Checks we're removing the useless tags correctly.'''
        
        # Get the stop tags regular expressions
        cwd = os.getcwd()
        parent = os.path.dirname(cwd)
        cfgs = os.path.join(parent, 'config/crowded.cfg')
        p = getConfigParameters(cfgs)
        
        # Get the tags
        f = open('./testResourceAssociatedTags.json', 'r')
        inTags = json.loads(f.read())
        #for tag in inTags:
        #    print tag
            
        print len(inTags)
        outTags = crowdedWorker.popUselessTags(p, inTags)
        print len(outTags)
        
        self.assertEquals(len(outTags), 1194)
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testGetTopTags']
    unittest.main()