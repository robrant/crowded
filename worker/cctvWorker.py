"""
0. Build a 1 minute cron that checks the subs collection for geos.
For each of these...
1. Make a call on the TFL URL
2. Check the length of the response
3. Loop the response and push the cams to the events collection

"""
import sys
import os
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
import urllib2
import json
import datetime
import mdb                  # Custom library for mongo interaction
from baseUtils import getConfigParameters
import crowdedWorker

#------------------------------------------------------------------------------------------ 
def getActiveSubs(collHandle, type='geography'):
    ''' Queries the subs collection for active subscriptions '''
    
    q = {'type':type} 
    res = collHandle.find(q)
    return [r for r in res]        

#------------------------------------------------------------------------------------------                 
def hitUrl(url):
    ''' Hits the feed and gets back the rss xml file.
        Need some error handling in here. '''
    
    print 'URL in hitUrl: %s' %url
    errors = []
    
    try:
        response = urllib2.urlopen(url)
    except Exception, e:
        print e
        errors.append(e)
        
    try:
        content = response.read()
    except Exception, e:
        print e
        errors.append(e)
        
    return errors, content

#------------------------------------------------------------------------------------------ 
def queryByGeo(url, lat, lon, radius):
    ''' Queries the remote service by geographical parameters. '''

    # Scale the radius back to metres     
    latScale, lonScale = crowdedWorker.radialToLinearUnits(float(lat))
    scale = (latScale + lonScale)/2.0
    print scale
    radius *= scale
    print radius
    
    url = url.replace('<event_latitude>', str(lat)) 
    url = url.replace('<event_longitude>', str(lon))
    url = url.replace('<event_radius_in_metres>', str(radius))
    
    print 'URL: %s' %url
    
    errors, data = hitUrl(url) 
    if len(errors) > 0:
        for error in errors:
            print error
    else:
        media = json.loads(data)
    
    print 'Media: %s' %(media)
    
    return media

#------------------------------------------------------------------------------------------ 
def queryByTag(p, url, tag):
    ''' Queries the subs collection for active subscriptions '''
    
    # Take in a url, add in the tag value
    
    # Submit to hitUrl
    
    # Load the response form json
    
    return 

#------------------------------------------------------------------------------------------ 
def updateEvents(collHandle, objectId, image):
    ''' Updates the media list in the events collection. '''
    
    # Query the collection first - does the media already exist in the collection.
    # Based simply on the standard resolution image
    # This compliments the byte-based check done in cams app
    filter = {'media.standard_resolution': image['standard_resolution'],
              'objectId' : objectId}
    
    exists = collHandle.find(filter).count()
    if exists > 0:
        success = 0

    else:
        try:
            # Establish the where clause
            filter = {'objectId':objectId}
            update = {'$push':{'media':image}}
            collHandle.update(filter, update)
            success = 1
        except Exception, e:
            print e
            success = None
    
    return success
          
#------------------------------------------------------------------------------------------ 
def main(configFile, subscriptionType, source):
    ''' Coordinates the retrieval of public CCTV camera URLs to crowded. '''
    
    # Get the config information into a single object
    p = getConfigParameters(configFile)
    
    #////////////////////////////////////////////////////////
    if source == 'cctv':
        url = p.tflUrl
    elif source == 'youtube':
        url = p.socialiseUrl
    elif source == 'flickr':
        url = p.viewFinderUrl
    # More sources here and adds to the config file
    #////////////////////////////////////////////////////////
        
    # Mongo connection parameters
    c, dbh = mdb.getHandle(host=p.dbHost, port=p.dbPort, db=p.db, user=p.dbUser, password=p.dbPassword)
    collHandle = dbh['subs']
    evCollHandle = dbh['events']
    
    # Get the active subs
    activeSubs = getActiveSubs(collHandle, type=subscriptionType)

    # Barf at this point if there's nothing in subs
    if not activeSubs or len(activeSubs) < 1:
        mdb.close(c, dbh)
        return None

    # For each active active subscription, query by geography
    for aSub in activeSubs:
        
        print 'ASUB:', aSub
        if subscriptionType == 'geography':
            lon, lat = aSub['loc']
            radius = float(aSub['radius'])
            media = queryByGeo(url, lat, lon, radius)
        
        elif subscriptionType == 'tag':
            tag = aSub['objectId']
            media = queryByTag(url, tag)
        
        # For each of the images, update the correct event url list
        for image in media:
            # Mod the datetime into a python dt
            try:
                img = datetime.datetime.strptime(image['captured'], "%Y-%m-%dT%H:%M:%S")
            except Exception, e:
                img = datetime.datetime.strptime(image['published'], "%Y-%m-%dT%H:%M:%S")
            image['dt'] = img    
            
            success = updateEvents(evCollHandle, aSub['objectId'], image)
            if success == None:
                print "Failed to update event ID '%s' with media: \n %s" %(aSub['objectId'], image)


if __name__ == '__main__':
    
    #try:
    configFile = sys.argv[1]
    subType    = sys.argv[2]
    source     = sys.argv[3]
    main(configFile, subType, source)

    #except Exception, e:
    #    print "Provide as arguments: config file path, subscription type (geography | tag) and source"
        
    