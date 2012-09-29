import os
import sys
import datetime
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

import mdb
from baseUtils import getConfigParameters
from instagram import InstagramAPI
from pymongo.son import SON

#///////////////////////////////////////////////////////////////////////////////////////////////
#
#///////////////////////////////////////////////////////////////////////////////////////////////

def checkForExistingSubs(p, subsCollHandle, event):
    ''' Check whether the subscription is already being monitored.
        If it is, replace its start date so that it doesn't get aged off.'''

    # Check for tag subscriptions of this value already in existence
    if event['object']=='tag':
        res = subsCollHandle.find_one({'objectId':event['tag']})
        if res and res.has_key('objectId'):
            exists = {'exists':True,'objectId':res['objectId'], 'object':event['object']}
            subsCollHandle.update({'objectId':event['tag']}, {'start':datetime.datetime.utcnow()})

        else:
            exists = {'exists':False}
    
    elif event['object']=='geography':
        
        query = SON({'$near':[event['lon'],event['lat']]})
        query['$maxDistance'] = event['radius']
        res = subsCollHandle.find_one({'loc' : query})
        
        if res and len(res.keys()) > 0:
            exists = {'exists':True, 'objectId':res['objectId'], 'object':event['object']}
        else:
            exists = {'exists':False}
        
    else:
            exists = {'exists':False}
    
    return exists

#------------------------------------------------------------------------------------------------------------

def checkGeos(lat=None, lon=None, radius=None, maxRad=5000):
    ''' Checks the validity of lat, lon and radius '''

    try:    lat = float(lat)
    except: lat = None
    try:    lon = float(lon)
    except: lon = None
    try:    radius = float(radius)
    except: radius = None

    if not lat or lat < -90.0 or lat > 90.0:
        lat = None
    
    if not lon or lon < -180.0 or lon > 180.0:
        lon = None

    if radius < 0.0 or radius > 5000.0:
        radius = None
        
    return lat, lon, radius

#------------------------------------------------------------------------------------------------------------

def updateSubs(subsCollHandle, subType, subId, objectId, aspect, event, user, protect=False):
    ''' Updates the subs collection with information relating to the subscription that has
        just been created on the instagram server. '''

    # Build the basic doc with flds common both geo and tag
    doc = {'type'     : subType,
           'subId'    : subId,
           'objectId' : objectId,
           'aspect'   : aspect,
           'user'     : user,
           'start'    : datetime.datetime.utcnow()}
    
    # Sparse field only used where it is true
    if protect==True:
        doc['protect'] = True
    
    # Add special fields for the geo-based subscriptions
    if event['object'] == 'geography':
        doc['loc'] = [event['lon'], event['lat']]
        doc['radius'] = event['radius']
    
    #print "Subscription document to be inserted:"
    #print doc
    
    # Insert the new record of a subscription
    _id = subsCollHandle.insert(doc)
    #print "ID of successfully inserted subscription doc: %s" %_id
    
    if _id:
        return objectId

#------------------------------------------------------------------------------------------------------------

def buildEventPlaceholder(evCollHandle, subType, event, objectId, protect=None):
    ''' Builds a new EVENT Document as a placeholder so all other events can be UPDATEs.'''

    doc = {"objectId" : objectId,
           "subType"  : subType,
           "start"    : datetime.datetime.utcnow(),
           "tags"     : {},
           "media"    : []}

    #print "Event placeholder."
    #print doc

    # Sparse field only used where it is true
    if protect==True:
        doc['protect'] = True

    if subType == 'geography':
        doc["loc"]    = [event['lon'], event['lat']]
        doc["radius"] = event['radius']

    _id = evCollHandle.insert(doc)
    #print "Id of successfully inserted event placeholder %s" %_id

    return _id

#------------------------------------------------------------------------------------------------------------

def buildSubscription(event):
    ''' Builds a new subscription based on an GET called event'''

    # Placeholder for doing this by users/algorithm?
    user = 'anon'

    cwd = os.getcwd()
    cfgs = os.path.join(cwd, 'config/crowded.cfg')
    p = getConfigParameters(cfgs)

    #print "Config Filepath in buildSubscription: ", cfgs

    # The mongo bits
    c, dbh = mdb.getHandle(host=p.dbHost, port=p.dbPort, db=p.db, user=p.dbUser, password=p.dbPassword)
    subsCollHandle = dbh[p.subsCollection]
    evCollHandle   = dbh[p.eventsCollection]
                
    # Check whether we definitely need a new subscription or not    
    checked = checkForExistingSubs(p, subsCollHandle, event)
    
    # If the subscription doesn't already exist, 
    if checked['exists'] == False:
        
        # Get the client and secret keys
        api = InstagramAPI(client_id=p.client, client_secret=p.secret)
    
        # If it's a geo-based subscription
        if event['object'] == 'geography':
            res = api.create_subscription(object='geography', lat=event['lat'], lng=event['lon'], radius=event['radius'],
                                    aspect='media', callback_url=p.subBaseUrl)
            print "Geo Subscription setup: %s" %res
        # A tag-based subscription
        elif event['object'] == 'tag':
            res = api.create_subscription(object='tag', object_id=event['tag'], aspect='media', callback_url=p.subBaseUrl)
            print "Tag Subscription setup: %s" %res
        # Just in case
        else:
            print 'Didnt setup a subscription' 
            res = None
    
        # Update the subscription collection 
        if res and res['meta']['code']==200:
    
            data = res['data']
            subType  = data['object'] 
            objectId = data['object_id'] 
            subId    = data['id']
            aspect   = data['aspect']
            success = updateSubs(subsCollHandle, subType, subId, objectId, aspect, event, user)
            
            # Build the response 
            response = {'success'  : True,
                        'objectId' : objectId,
                        'object'   : subType,
                        'url'      : "%s/%s" %(p.baseUrl, success)}
        
            # Insert a blank document to populate
            _id = buildEventPlaceholder(evCollHandle, subType, event, objectId)
            
        # Something failed in the subscription build...?
        else:
            print '='*40
            print 'Failed here. No event placeholder or subscription updated.'
            print res
            print '='*40
            response = {'success'  : False,
                        'objectId' : checked['objectId'],
                        'object'   : checked['object'],
                        'url'      : "%s/%s" %(p.baseUrl, checked['objectId'])}
    
    # A valid subscription already exists 
    elif checked['exists'] == True:
        response = {'success'  : True,
                    'objectId' : checked['objectId'],
                    'object'   : checked['object'],
                    'url'      : "%s/%s" %(p.baseUrl, checked['objectId'])}

    # Close the connection/handle
    mdb.close(c, dbh)

    return response
