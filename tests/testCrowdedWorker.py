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
import datetime
from random import randint

class Test(unittest.TestCase):

    """
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
    
    def testReorderMedia(self):
        ''' Re-orders the media provided - no limit.'''
        
        media = []
        
        for i in range(10):
            image = {'dt' : datetime.datetime.utcnow() + datetime.timedelta(seconds=randint(0,300)),
                     'caption': 'caption %s' %i,
                     "low_resolution":"http://distilleryimage4.s3.amazonaws.com/0a3e189a0d1911e289de22000a1cf722_6.jpg",
                     "standard_resolution":"http://distilleryimage4.s3.amazonaws.com/0a3e189a0d1911e289de22000a1cf722_7.jpg",
                     "source":"instagram",
                     "thumbnail":"http://distilleryimage4.s3.amazonaws.com/0a3e189a0d1911e289de22000a1cf722_5.jpg"}
            media.append(image)
        
        outMedia = crowdedWorker.reorderMedia(media)
        for me in outMedia:
            print me['dt']

    def testReorderMedia(self):
        ''' Re-orders the media provided - with limit.'''
        
        media = []
        
        for i in range(100):
            image = {'dt' : datetime.datetime.utcnow() + datetime.timedelta(seconds=randint(0,300)),
                     'caption': 'caption %s' %i,
                     "low_resolution":"http://distilleryimage4.s3.amazonaws.com/0a3e189a0d1911e289de22000a1cf722_6.jpg",
                     "standard_resolution":"http://distilleryimage4.s3.amazonaws.com/0a3e189a0d1911e289de22000a1cf722_7.jpg",
                     "source":"instagram",
                     "thumbnail":"http://distilleryimage4.s3.amazonaws.com/0a3e189a0d1911e289de22000a1cf722_5.jpg"}
            media.append(image)
        
        outMedia = crowdedWorker.reorderMedia(media, 10)
        for me in outMedia:
            print me['dt']

    def testCopyf(self):
        ''' Filters a list of dictionaries. '''
        
        x = [
             {u'start': datetime.datetime(2012, 10, 6, 9, 32, 27, 718000), u'objectId': u'robbery', u'subType': u'tag'},
             {u'start': datetime.datetime(2012, 10, 6, 9, 36, 30, 242000), u'objectId': u'pti', u'subType': u'tag'},
             {u'loc': [-0.13089999999999999, 51.516199999999998], u'objectId': u'1506208', u'start': datetime.datetime(2012, 10, 6, 9, 28, 25, 64000), u'subType': u'geography', u'radius': 0.0022139325980523698, 'bbox': [[-0.13311393259805235, 51.513986067401945], [-0.12868606740194763, 51.518413932598051]], 'radius_m': 200},
             {u'start': datetime.datetime(2012, 10, 6, 9, 35, 7, 510000), u'objectId': u'protest', u'subType': u'tag'},
             {u'loc': [-0.128723, 51.526896999999998], u'objectId': u'1506153', u'start': datetime.datetime(2012, 10, 6, 8, 45, 12, 968000), u'subType': u'geography', u'radius': 0.0055353234321957054, 'bbox': [[-0.13425832343219571, 51.5213616765678], [-0.1231876765678043, 51.532432323432197]], 'radius_m': 499},
             ]
        
        geoEvents = crowdedWorker.copyf(x, 'subType', ['geography'])
        self.assertEquals(len(geoEvents),2)
        
        tagEvents = crowdedWorker.copyf(x, 'subType', ['tag'])
        self.assertEquals(len(tagEvents),3)
        
                        
    def testgetEvents(self):
        ''' Queries the mongodb to return all active events.'''
        
        cwd = os.getcwd()
        parent = os.path.dirname(cwd)
        cfgs = os.path.join(parent, 'config/crowdedForTestGetEvents.cfg')
        p = getConfigParameters(cfgs)
        
        outEvents = crowdedWorker.getEvents(p)
        for e in outEvents:
            print e

    """
        
    def testvalidMediaCheck(self):
        ''' Makes sure the media is correctly formatted before being pushed in'''
    
        testCase = {"standard_resolution" : "http://distilleryimage1.s3.amazonaws.com/8b74d2ee0e5611e2adc122000a1de653_7.jpg",
                    "low_resolution" : "http://distilleryimage1.s3.amazonaws.com/8b74d2ee0e5611e2adc122000a1de653_6.jpg",
                    "source" : "instagram",
                    "dt" : "2012-10-04T19:06:04Z",
                    "caption" : "NOH8 CAMPAGIN #selfmade #wtwd #ducttape #chicago",
                    "thumbnail" : "http://distilleryimage1.s3.amazonaws.com/8b74d2ee0e5611e2adc122000a1de653_5.jpg",
                    "objectId" : 'foobar'
                    }

        cwd = os.getcwd()
        parent = os.path.dirname(cwd)
        cfgs = os.path.join(parent, 'config/crowded.cfg')
        p = getConfigParameters(cfgs)
        
        nm = crowdedWorker.validMediaCheck(p, testCase)
        self.assertEquals(len(nm['errors']), 0)
        
    def testvalidMediaCheck_BAD_DATETIME(self):
        ''' Makes sure the media is correctly formatted before being pushed in'''
    
        testCase = {"standard_resolution" : "http://distilleryimage1.s3.amazonaws.com/8b74d2ee0e5611e2adc122000a1de653_7.jpg",
                    "low_resolution" : "http://distilleryimage1.s3.amazonaws.com/8b74d2ee0e5611e2adc122000a1de653_6.jpg",
                    "source" : "instagram",
                    "dt" : "2012-10-04T19:06:04.0Z",
                    "caption" : "NOH8 CAMPAGIN #selfmade #wtwd #ducttape #chicago",
                    "thumbnail" : "http://distilleryimage1.s3.amazonaws.com/8b74d2ee0e5611e2adc122000a1de653_5.jpg",
                    "objectId" : 'foobar'
                    }

        cwd = os.getcwd()
        parent = os.path.dirname(cwd)
        cfgs = os.path.join(parent, 'config/crowded.cfg')
        p = getConfigParameters(cfgs)
        
        nm = crowdedWorker.validMediaCheck(p, testCase)
        self.assertEquals(len(nm['errors']), 1)
                
    def testvalidMediaCheck_NO_STANDARD_RESOLUTION(self):
        ''' Makes sure the media is correctly formatted before being pushed in'''
    
        testCase = {"low_resolution" : "http://distilleryimage1.s3.amazonaws.com/8b74d2ee0e5611e2adc122000a1de653_6.jpg",
                    "source" : "instagram",
                    "dt" : "2012-10-04T19:06:04Z",
                    "caption" : "NOH8 CAMPAGIN #selfmade #wtwd #ducttape #chicago",
                    "thumbnail" : "http://distilleryimage1.s3.amazonaws.com/8b74d2ee0e5611e2adc122000a1de653_5.jpg",
                    "objectId" : 'foobar'
                    }

        cwd = os.getcwd()
        parent = os.path.dirname(cwd)
        cfgs = os.path.join(parent, 'config/crowded.cfg')
        p = getConfigParameters(cfgs)
        
        nm = crowdedWorker.validMediaCheck(p, testCase)
        self.assertEquals(len(nm['errors']), 1)
        print nm['errors']
                
"""
Example successful media for upload.

{"data":[{"standard_resolution" : "http://distilleryimage1.s3.amazonaws.com/8b74d2ee0e5611e2adc122000a1de653_7.jpg",
          "low_resolution" : "http://distilleryimage1.s3.amazonaws.com/8b74d2ee0e5611e2adc122000a1de653_6.jpg",
           "source" : "instagram",
           "dt" : "2012-10-04T19:06:04Z",
           "caption" : "This actually worked as a POST",
           "thumbnail" : "http://distilleryimage1.s3.amazonaws.com/8b74d2ee0e5611e2adc122000a1de653_5.jpg",
           "objectId" : "snorty",
           "tags" : ["hello world", "foo", "bar"]}]}



"""        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testGetTopTags']
    unittest.main()