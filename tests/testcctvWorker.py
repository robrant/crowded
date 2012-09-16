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
import cctvWorker
from baseUtils import getConfigParameters

class Test(unittest.TestCase):

    def testqueryByGeo(self):
        ''' Queries by geo.'''
        
        tflUrl = 'http://cams-redsquirrel.dotcloud.com/tfl?lat=<event_latitude>&lon=<event_longitude>&radius=<event_radius_in_metres>'
        lon=0.0886
        lat=51.45549
        radius=500
        
        outMedia = cctvWorker.queryByGeo(tflUrl, lat, lon, radius)
        self.assertEquals(outMedia[0]['caption'], 'a2 east rochester way by falconwood')
       
    """ 
    def testqueryByTag(self):
        ''' Queries by tag.'''
        
        tflUrl = 'http://cams-redsquirrel.dotcloud.com/tfl?lat=<event_latitude>&lon=<event_longitude>&radius=<event_radius_in_metres>'
        lon=0.0886
        lat=51.45549
        radius=500
        
        outMedia = cctvWorker.queryByGeo(tflUrl, lat, lon, radius)
        self.assertEquals(outMedia[0]['caption'], 'a2 east rochester way by falconwood')
    """

        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testGetTopTags']
    unittest.main()