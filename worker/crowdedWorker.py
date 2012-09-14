import os
import sys
import operator

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
from operator import itemgetter
import json
import urllib2
from pymongo import DESCENDING
#import jmsCode                      # JMS STOMP connection wrapper - needs stomp.py
import datetime
import mdb
import re

#///////////////////////////////////////////////////////////////////////////////////////////////
#
# Set of functions to handle the update payload from an instagram subscription update POST. 
#
# The main() seems a bit convoluted, but it handles the possibility of multiple updates in a 
# single POST. And then it handles each media item (photo) returned from the GET call the the
# relevant search endpoint.
# 
# It also handles the recording of the next URL, so that each call only gets the most recent
# content that has not been retrieved before. It does that by retrieving either a 'min_id' (in the
# case of the geography) or a 'next_url' (in the case of a tag) and storing this for the next time.
#
# The next URL (from geog and from tag) is stored in a text file named according to the object_id
# for the subscription in the /config directory. The code attempts to open this for every update
# and read the next url. If it can't, it just proceeds in getting all that is available.
#
# Media metadata is either put out over JMS (not tested yet) or dumped straight to a file as JSON.
#
# If on dotcloud, check /var/log/supervisor/uwsgi.log for any print outs/errors.
# Also, note that if deploying on dotcloud you will need a custom build to ensure nginx can 
# accept big enough POST payloads.
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

def updateImageUrls(evCollHandle, objectId, metadata):
    ''' Updates the urls on file against this tag or location. '''
    
    res = 1
    
    imageOut = {}
    # The query to find the correct event document
    filter = {'objectId':objectId}
    
    # Get the image urls (they take a 
    images = metadata['images']
    for image in images.keys():
        imageOut[image] = images[image]['url']
    
    # Append the datetime information
    #dt = datetime.datetime.fromtimestamp(float(metadata['created_time']))
    #imageOut['dt'] = dt.strftime('%H:%M:%SZ on %a %d %b %Y')
    try:
        imageOut['dt']= datetime.datetime.fromtimestamp(float(metadata['created_time']))
    except:
        imageOut['dt']= datetime.datetime.utcnow()
        imageOut['dt_est'] = True
        
    # Put a source on it for further filtering
    imageOut['source'] = 'instagram'
    
    # Append the caption for this image
    try:
        imageOut['caption'] = metadata['caption']['text']
    except:
        imageOut['caption'] = "** caption text not parsed **"
    # Conduct the update
    try:
        update = {'$push':{'media':imageOut}}
        evCollHandle.update(filter, update, upsert=True)
    except Exception, e:
        print e
        res = 1
    
    return res

#------------------------------------------------------------------------------------------------

def getMediaUpdates(url):
    ''' Reads and parses the subscription updates'''
  
    try:
        response = urllib2.urlopen(url)
        mediaMeta = json.loads(response.read())
    except:
        mediaMeta = None
        print "Failed to open this url: \n %s" %url
        
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

def reorderMedia(media, limit=100):
    ''' Reorders the media by its date time field. '''

    outMedia = newlist = sorted(media, key=itemgetter('dt'), reverse=True) 
    media = outMedia[:limit]

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
        url = getNextUrl(p, objectId)
        
        # If the next (ie this) url hasn't been written to a file, build it from the config file 
        if url == None:
            url = buildUrl(p, objectType, objectId)
        
        # Get the media that has changed since the last time
        mediaMeta = getMediaUpdates(url)    
        
        # Find the pagination info and save out info that concerning next url for this subscription
        handleMediaPagination(p, url, objectId, mediaMeta)

        # Update the tags and urls arrays
        if mediaMeta.has_key('data'):
            for photo in mediaMeta['data']:
                
                res = updateImageUrls(evCollHandle, objectId, photo)
                res = updateTags(evCollHandle, objectId, photo)
            
         