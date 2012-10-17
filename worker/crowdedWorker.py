import os
import sys
import operator
import math
import time
from operator import itemgetter
import json
import urllib2
import datetime
import re
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
from pymongo import DESCENDING
import mdb

#///////////////////////////////////////////////////////////////////////////////////////////////
#
# Remove instagram specific code from here.
# 1 file to contain the management functions for the site - listing current events, destroying events, etc
# 1 file to contain the splash page functions (retrieve all, retrieve secific, etc
# write tests for all possible
#    
#
#///////////////////////////////////////////////////////////////////////////////////////////////

def getNextUrl(p, object_id):
    ''' See whether the url to use has already been written to a file '''
    
    outDir = os.path.dirname(p.configFile)
    if str(object_id) in os.listdir(outDir):
        f = open(os.path.join(outDir, str(object_id)), 'r')
        url = f.read()
        f.close()
    else:
        url = None
        
    return url
#--------------------------------------------------------------------------------------------

def radialToLinearUnits(latitude):
    
    ''' Calculates the length of 1 degree of latitude and longitude at
        a given latitude. Takes as arguments the latitude being worked at.
        Returns the length of 1 degree in metres. NEEDS TESTING '''
    
    # Work in radians
    lat = math.radians(latitude)
    
    # Constants
    m1 = 111132.92
    m2 = -559.82
    m3 = 1.175
    m4 = -0.0023
    p1 = 111412.84
    p2 = -93.5
    p3 = 0.118
    
    # Length of a degree in Latitude
    latLen = m1 + (m2 * math.cos(2 * lat)) + (m3 * math.cos(4 * lat)) + \
             (m4 * math.cos(5 * lat))
             
    lonLen = (p1 * math.cos(lat)) + (p2 * math.cos(3*lat)) + (p3 * math.cos(5*lat))
        
    return latLen, lonLen

#------------------------------------------------------------------------------------------------

def popUselessTags(p, tags):
    ''' Removes useless tags based on a regex against certain known useless tags.'''
    
    configDir = os.path.dirname(p.configFile)
    regExpsFile = open(os.path.join(configDir, 'stopTags.txt'), 'r')
    
    popList = []
    for line in regExpsFile:
        if line.startswith(' ') or line.startswith('#'):
            continue

        reg    = line.rstrip('\n')
        reg    = line.strip()
        regExp = re.compile(reg)
        for tag in tags.keys():
            out = re.search(reg, tag)
            try:
                grps = out.groups()
                #print 'grps here', grps
                if len(grps) == 0:
                    grps = None
            except:
                grps = None
            
            if grps:
                popList.append(tag)
        
    # Loop the tags and the regular expressions
    for popper in popList:
        try:
            tags.pop(popper)
        except:
            pass
        
    return tags

#------------------------------------------------------------------------------------------------

def filterTagsByPercentCount(tags, primary, thresh=0.1):
    ''' Whittles down the tags into a useful group by rank.
        tags is a dictionary = {'tag1':3, 'tag2': 6, 'tag3': 1}'''
    
    # Get rid of the primary tag
    try:
        tags.pop(primary.lower())
    except:
        pass
    
    # Sort the dictionary based on the count - number of times that tag was observed alongside this one
    sortedTags = sorted(tags.iteritems(), key=operator.itemgetter(1))        
    
    # Get the min and max and calculate a threshold to pull out the interesting ones
    minVal = sortedTags[0][1]
    maxVal = sortedTags[-1][1]
    countRange = (maxVal - minVal)
    threshold = float(countRange) * (1-thresh)
    
    # Return the top x% of tags, based on how often associated with the main tag
    outTags = [] 
    for tag in reversed(sortedTags):
        if tag[1] > threshold:
            outTags.append("%s(%s)" %tag)
    
    return outTags
    
#------------------------------------------------------------------------------------------------

def filterTagsByCount(tags, primary, numberTopTags=15):
    ''' Whittles down the tags into a useful group by rank.
        tags is a dictionary = {'tag1':3, 'tag2': 6, 'tag3': 1} Takes the top x tags'''

    # Get rid of the primary tag
    try:
        tags.pop(primary.lower())
    except:
        pass
    
    # Sort the dictionary based on the count - number of times that tag was observed alongside this one
    sortedTags = sorted(tags.iteritems(), key=operator.itemgetter(1), reverse=True)
    if len(sortedTags) < numberTopTags:
        numberTopTags = len(sortedTags)
    sortedTags = sortedTags[:numberTopTags]

    outTags = [] 
    for tag in sortedTags:
            outTags.append("%s(%s)" %tag)
    
    return outTags

#------------------------------------------------------------------------------------------------

def updateTags(evCollHandle, objectId, metadata):
    ''' Updates the tags on file against this tag or location event. '''
    
    res = 1
    # The query to find the correct event document
    filter = {'objectId':objectId}
    
    # Get the image urls (they take a 
    for tag in metadata['tags']:

        try:
            update = {'$inc':{'tags.%s' %(tag) : 1}}
            evCollHandle.update(filter, update, upsert=True, multi=True)
        except:
            res = None
    
    return res
    
#------------------------------------------------------------------------------------------------

def updateImageUrls(evCollHandle, objectId, metadata, dt):
    ''' Updates the urls on file against this tag or location. '''
    
    imageOut = {'dt':dt,
                'source':'instagram'}
    res = 1
    
    # The query to find the correct event document
    filter = {'objectId': objectId}
        
    # Get the image urls (they take a 
    images = metadata['images']
    for image in images.keys():
        imageOut[image] = images[image]['url']
        
    # Append the caption for this image
    try:
        imageOut['caption'] = metadata['caption']['text']
    except Exception, e:
        print e
        imageOut['caption'] = "** caption text not parsed **"
    # Conduct the update
    try:
        update = {'$push':{'media':imageOut}}
        #print "Filter:", filter
        #print "Update:", update
        evCollHandle.update(filter, update, upsert=True)
    except Exception, e:
        print e
        res = 0

    return res

#------------------------------------------------------------------------------------------------

def updateLatestInfo(evCollHandle, objectId, latest):
    ''' Updates the document with the latest image time.'''
    
    # The query to find the correct event document
    filter = {'objectId': objectId}
    update = {'$set'  : {'latest': latest}}    
    
    try:
        evCollHandle.update(filter, update, upsert=True)
    except Exception, e:
        print e
        print "Failed to update the 'latest' field with '%s'" %latest
        
#------------------------------------------------------------------------------------------------

def retrieveLatestImage(evCollHandle, objectId):
    ''' Gets the time of the last image in the doc'''
    
    # Get the most recent time for this document
    try:
        doc    = evCollHandle.find_one({'objectId':objectId})
        latest = doc['latest']
    except Exception, e:
        print '_-'*40
        print e
        print '_-'*40
        latest = None

    return latest

#------------------------------------------------------------------------------------------------

def getMediaUpdates(url):
    ''' Reads and parses the subscription updates'''

    try:
        response = urllib2.urlopen(url)
        mediaMeta = json.loads(response.read())
    except urllib2.HTTPError:
        mediaMeta = None
        
    return mediaMeta 

#------------------------------------------------------------------------------------------------

def handleMediaPagination(p, url, object_id, mediaMeta):
    ''' Extracts the pagination information relating to the next set of update data'''

    nextUrl = None
    
    # See if there is a pagincation key in the media metadata
    if mediaMeta and mediaMeta.has_key('pagination'):
        pagination = mediaMeta['pagination']
        
        # If it has a next_url, then get that for the next time this gets updated - they tell you what its going to be
        if pagination.has_key('next_url') and pagination['next_url'] != None:
            nextUrl = pagination['next_url']
        
        # Geography subscriptions, just have a next_min_id, which is used to get the next data. 
        elif pagination.has_key('next_min_id') and pagination['next_min_id'] != None:
            minId = pagination['next_min_id']
            
            # Strip out the base url. Catch the first instance where it shouldn't have an & in it
            amp = url.find('&')
            if amp != -1:
                url = url[:amp+1]
            nextUrl = "%s&min_id=%s" %(url, minId)
            
        else:
            pass
            
    else:
        print "Failed too retrieve either mediaMeta or the pagination key."
        
    # Where we've been successful getting the next url, dump it out to a file for next time
    if nextUrl:
        try:
            outDir = os.path.dirname(p.configFile)
            outName = os.path.join(outDir, str(object_id))
            fOut = open(outName, 'w')
            fOut.write(nextUrl)
            fOut.close()
        except:
            print "Failed to write out next URL for object_id : %s \n %s" %(object_id, nextUrl)
    
    return
#------------------------------------------------------------------------------------------------

def buildUrl(p, obj, objectId):
    ''' Submits the request to the SEARCH api for the actual media update.
        This gets called if the pagination function doesn't get used.
        The pagination function gets the 'next' url from the current message,
        That url ensures you don't get dupes.'''
    
    # Swap out the geography id
    if obj == 'geography':
        url = p.geoUrl.replace('<geo-id>', str(objectId))

    # Swap out the tag
    if obj == 'tag':
        url = p.tagUrl.replace('<tag>', str(objectId))
        
    # Sub out the client id for authorisation
    url = url.replace('<client-id>', str(p.client))
    
    return url

#------------------------------------------------------------------------------------------------

def reorderMedia(media, limit=None):
    ''' Reorders the media by its date time field. '''

    media.sort(key=itemgetter('dt'), reverse=True) 
    if limit and limit < len(media):
        media = media[:limit]

    return media

#------------------------------------------------------------------------------------------------

def getMediaByObjectId(p, objectId):
    ''' Gets a mongo doc back based on the object ID. Called by the display page. '''

    # The mongo bits
    c, dbh = mdb.getHandle(host=p.dbHost, port=p.dbPort, db=p.db, user=p.dbUser, password=p.dbPassword)
    evCollHandle = dbh[p.eventsCollection]    

    # The query into mongo that should only return 1 doc
    query = {'objectId' : objectId}
    doc = evCollHandle.find(query)
    
    try:
        doc = [d for d in doc][0]
    except:
        print "No document matched your query. Object ID: %s." %objectId
        doc = None
    mdb.close(c, dbh)

    return doc

#------------------------------------------------------------------------------------------------

def copyf(dictList, key, valueList):
    ''' Returns a filtered list of dictionaries'''
    
    if not dictList or not key or not valueList:
        out = []
    else:
        out = [dictio for dictio in dictList if dictio[key] in valueList]
    return out

#------------------------------------------------------------------------------------------------

def getEvents(p):
    ''' Returns all currently active events in mongo '''
    
    # The mongo bits
    c, dbh = mdb.getHandle(host=p.dbHost, port=p.dbPort, db=p.db, user=p.dbUser, password=p.dbPassword)
    evCollHandle = dbh[p.eventsCollection]  
    
    try:
        docs = evCollHandle.find(fields=['objectId','subType','start','loc','radius'])
        docsOut = [d for d in docs]
        
    except:
        print "No documents matched your query. Object ID: %s." %objectId
        docsOut = []
    mdb.close(c, dbh)
    
    # Additional fields that might be useful
    for doc in docsOut:
        # Get rid of the mongo ID
        _id = doc.pop('_id')
        
        if doc.has_key('loc'):
            
            # calculate the radius in metres
            latScale, lonScale = radialToLinearUnits(float(doc['loc'][1]))
            scale = (latScale + lonScale)/2.0
            doc['radius_m'] = int(doc['radius'] * scale)
        
            # Calculate the top left, bottom right
            s = doc['loc'][1] - doc['radius']
            w = doc['loc'][0] - doc['radius']
            n = doc['loc'][1] + doc['radius']
            e = doc['loc'][0] + doc['radius']
            doc['bbox'] = [[w,s],[e,n]]
                         
    return docsOut

#------------------------------------------------------------------------------------------------
    
def validMediaCheck(p, media):
    ''' For POST functions, checks that the media json is valid and good to be inserted'''

    newMedia = {} 
    valid = True
    # Check that the objectId exists in mongo
    try:
        objectId = media.pop('objectId')
    except:
        valid = False
        objectId = None
        logging.error("Failed to get the objectId from the incoming POST payload\n %s" %(media), exc_info=True)
    # Extract the tags
    try:
        tags = media.pop('tags')
    except:
        valid = False
        tags = None
        logging.error("Failed to get tags from incoming POST payload\n %s" %(media), exc_info=True)
    
    # Check all of the other fields are present
    for fld in p.mediaFlds:
        if fld in media.keys():
            newMedia[fld] = media[fld]
        else:
            logging.warning('payload json does not contain field: %s.' %(fld))

    # Format the dt info into a datetime
    try:
        newMedia['dt'] = datetime.datetime.strptime(newMedia['dt'], "%Y-%m-%dT%H:%M:%S")
    except:
        valid = False
        logging.warning('Failed to process datetime: %s' %(newMedia['dt']))

    return valid, objectId, newMedia, tags
    
#------------------------------------------------------------------------------------------------

def updateEventMedia(evCollHandle, objectId, media, tags):
    ''' Pushes the new media item into the mongo collection. '''

    res = 1
    
    # The query to find the correct event document
    filter = {'objectId': objectId}
    doc = evCollHandle.find_one(filter)
    if doc or doc.has_key('media'):
            
        # Update the media
        try:
            update = {'$push':{'media':media}}
            evCollHandle.update(filter, update)
        except:
            logging.error('Failed to push new media: %s' %(media), exc_info=True)
            res = 0
            
        # Update the tag information
        try:
            res = updateTags(evCollHandle, objectId, {'tags':tags})
        except:
            logging.error('Failed to updates tags: %s' %(tags), exc_info=True)
            res = 0
    else:
        res = -1
        
    return res

#------------------------------------------------------------------------------------------------

def main(p, response):
    '''Handles the subscription updates, including making the call to the endpoint and dumping to jms/text.'''
    
    # The mongo bits
    c, dbh = mdb.getHandle(host=p.dbHost, port=p.dbPort, db=p.db, user=p.dbUser, password=p.dbPassword)
    evCollHandle = dbh[p.eventsCollection]
    
    # Accepts a list of dictionaries - the update message
    updates = json.loads(response)

    # Format the url and get the media metadata
    for upd in updates:
        
        objectId = upd['object_id']
        objectType =  upd['object']
        # Does the next URL already exist for this object?
        #url = getNextUrl(p, objectId)
        
        # If the next (ie this) url hasn't been written to a file, build it from the config file 
        #if url == None or len(url) < 1:
        url = buildUrl(p, objectType, objectId)
        
        # Get the media that has changed since the last time
        mediaMeta = getMediaUpdates(url)    
        
        # Find the pagination info and save out info that concerning next url for this subscription
        #handleMediaPagination(p, url, objectId, mediaMeta)

        # Get the last insert time
        lastUpdated = retrieveLatestImage(evCollHandle, objectId)
        latest      = time.mktime(lastUpdated.timetuple())
        newLatest   = time.mktime(lastUpdated.timetuple())

        # Update the tags and urls arrays
        if mediaMeta and mediaMeta.has_key('data'):
            #print "Number of Images:", len(mediaMeta['data'])
            for photo in mediaMeta['data']:
                
                # Append the datetime information
                try:
                    epochTime = float(photo['created_time'])
                    dt = datetime.datetime.fromtimestamp(epochTime)
                except Exception, e:
                    print e
                
                # For recent images
                if epochTime > latest:
                    # Update the list of images stored
                    res = updateImageUrls(evCollHandle, objectId, photo, dt)
                    # Update the tag information
                    res = updateTags(evCollHandle, objectId, photo)
                
                # Get the latest image datetime
                if epochTime > newLatest:
                    #print "improving newLatest", epochTime, newLatest
                    newLatest = epochTime
            
            # Update the latest datetime on record
            updateTimeStamp = datetime.datetime.fromtimestamp(newLatest)
            updateLatestInfo(evCollHandle, objectId, updateTimeStamp)