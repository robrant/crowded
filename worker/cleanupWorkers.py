import os
import sys
import logging
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

import mdb
from baseUtils import getConfigParameters
import datetime
from instagram import InstagramAPI

#///////////////////////////////////////////////////////////////////////////////////////////////
#
# Description:
# ------------
# Provides functions for cleaning up instagram subscriptions (pubsubhubub) and media metadata 
# stored in the mongo collection. 
#
# To do:
# ------
# Should gather the list of subscriptions from the instagram server as well as from mongo. Just
# to check they're the same. Some have slipped through before when there have been bugs in the 
# code.

#///////////////////////////////////////////////////////////////////////////////////////////////


def getExpiredSubs(collHandle, ageOff=4, protectedSubs=None):
    ''' Retrieves a list of expired subscriptions '''

    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=ageOff/24.0)
    q = {'start':{'$lte':cutoff}}

    if protectedSubs:
        q['protect'] = protectedSubs
        
    # Get a list of subs that need aging off
    res = collHandle.find(q)
    print 'Subs Query: ', q
    
    # One used to clean the sub on instagram. ObjectIds used to clean the config dir
    oldSubs, oldObjectIds = [], []
    for r in res:
        print r
        oldSubs.append(r['subId'])
        oldObjectIds.append(r['objectId'])

    res = collHandle.remove(q)

    return oldSubs, oldObjectIds


#------------------------------------------------------------------------------------------------------------

def ageOffSubscriptions(p, collHandle, ageOff, protectedSubs):
    ''' Deletes subscriptions from the Instagram server based on the age and protection level
        in the subs collection. If protect=True, then it must be manually deleted'''

    out = []
    
    # Get the client and secret keys
    api = InstagramAPI(client_id=p.client, client_secret=p.secret)

    # Get the expired non-protected subscriptions
    subs, ids = getExpiredSubs(collHandle, ageOff, protectedSubs)
    
    # Delete the subscriptions from the instagram server
    for sub in subs:
        print sub
        deleted = api.delete_subscriptions(id=int(sub))
        print deleted
        out.append(deleted)
        if deleted['meta']['code'] != 200:
            print 'Failed to delete subscription %s' %(sub)

    # Delete the nextUrl object files (kept in the config directory)
    for objId in ids:
        f = os.path.join(os.path.dirname(p.configFile), objId)
        try:
            os.remove(f)
        except:
            print 'Failed to delete the subscription next URL file: \n %s\n' %(f)
            
    return out

#------------------------------------------------------------------------------------------------------------

def ageOffMetadata(collHandle, ageOff, protectMedia=None):
    ''' Deletes the metadata that is older than 'ageOff' stored in the events db. '''

    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=ageOff/24.0)
    q = {'start':{'$lte':cutoff}}
    
    if protectMedia:
        q['protect'] = protectMedia
    # Get a list of subs that need aging off
    #res = collHandle.find(q)
    #oldEvents = [i['subId'] for i in res]
    print 'Event Query: ', q
    res = collHandle.remove(q)

    return res

#------------------------------------------------------------------------------------------------------------

def main(cleanup, ageOff, protectedSubs=None):
    ''' Coordinates which element to cleanup - subscriptions including remote delete of subs from instagram
        or event data - getting rid of the documents that contain the media and metadata'''
    
    # If there is a command to remove or keep protected subs, use it
    if protectedSubs:
        protectedSubs = bool(protectedSubs)
    
    # Get the config information
    os.chdir('/home/dotcloud/code/')
    cwd  = os.getcwd()
    cfgs = os.path.join(cwd, 'config/crowded.cfg')
    p = getConfigParameters(cfgs)
    
    # The mongo bits
    c, dbh = mdb.getHandle(host=p.dbHost, port=p.dbPort, db=p.db, user=p.dbUser, password=p.dbPassword)

    # Whether to cleanup the subscriptions and subscription collection
    if cleanup == 'subs':
        subsCollHandle=dbh[p.subsCollection]
        res = ageOffSubscriptions(p, subsCollHandle, ageOff=ageOff, protectedSubs=protectedSubs)
        print datetime.datetime.utcnow(), res
    
    # Or the events metadata collection
    elif cleanup == 'events':
        evCollHandle=dbh[p.eventsCollection]
        res = ageOffMetadata(evCollHandle, ageOff=ageOff, protectMedia=protectedSubs)
        print datetime.datetime.utcnow(), res
        
    else:
        print 'Provide either subs or events as the first argument depending on what you want to clean up.'


if __name__ == '__main__':
    
    # Don't clear the protected subs
    if len(sys.argv) == 3:
        cleanupType = sys.argv[1] 
        ageOffHours = float(sys.argv[2]) 
        main(cleanupType, ageOffHours)
    
    # Where we want to clear the protected subs also
    elif len(sys.argv) == 4: 
        cleanupType = sys.argv[1] 
        ageOffHours = float(sys.argv[2]) 
        protectedSubs = sys.argv[3]
        main(cleanupType, ageOffHours, protectedSubs)
    
    else:
        print "---- Cleanup operation requires 2 arguments:"
        print "----   cleanupType = subs | events"
        print "----   ageOffHours = <the minimum age of subscription to keep (in Hours)>"
        print "---- It also has an optional cleanup of protected subscriptions too: boolean"
    
