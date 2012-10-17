import os
import sys
import bottle
import json
import logging

from bottle import route, post, run, request, static_file, template, redirect
#from instagram import client, subscriptions

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
import datetime

from baseUtils import getConfigParameters
import crowdedWorker
import subscriptionWorker
import mdb
bottle.debug(True)

#///////////////////////////////////////////////////////////////////////////////////////////////
#
# Crowded:
# ========
# 
# Description:
# ------------
# - Provides a crowd sourced perspective of events as they happen through a single gallery splash page
# - Does so through wsgi (in your web server of choice)
# - This module provides the url-routing functions.
#
#
# To do:
# -----
# - Is it possible to support multiple wsgi files for a single application?
# - If so, break out the admin functions.
# - Look into using twisted as the framework or web server so that it is FAST to receive the POSTs
#   from external sources
#   Extract the instagram bits from this code.


#///////////////////////////////////////////////////////////////////////////////////////////////

os.chdir('/home/dotcloud/current/')
cwd = os.getcwd()
cfgs = os.path.join(cwd, 'config/crowded.cfg')
p = getConfigParameters(cfgs)

# The mongo bits
c, dbh = mdb.getHandle(host=p.dbHost, port=p.dbPort, db=p.db, user=p.dbUser, password=p.dbPassword)
evCollHandle = dbh[p.eventsCollection] 

logFile = os.path.join(p.errorPath, p.errorFile)
logging.basicConfig(filename=logFile, format='%(levelname)s:: \t%(asctime)s %(message)s', level='DEBUG')

#------------------------------------------------------------------------------------------------

def on_error(errFile='errors.txt', message=None):
    ''' Handles an error message '''
    
    f = open(os.path.join(cwd, errFile), 'a')
    f.write(message + '\n')
    f.close()

#------------------------------------------------------------------------------------------------
@route('/list_events')
@route('/manage_events')
@route('/events')
@route('/events/')

def listEvents():
    ''' List all events in the db. '''
    
    htmlPage = bool(request.query.html)
    
    # Perform management function
    events = crowdedWorker.getEvents(p)
    for event in events:
        
        if event.has_key('start') == False:
            continue
        event['start'] = event['start'].isoformat()
    
    # If the user wants it rendered to a page
    if htmlPage == True:
        # Split up the geo from the tag-based events
        geoEvents = crowdedWorker.copyf(events, 'subType', ['geography'])
        tagEvents = crowdedWorker.copyf(events, 'subType', ['tag'])

        # Reformat some of the geo info
        for geo in geoEvents:
            geo['loc'][0] = str(geo['loc'][0])[:6]
            geo['loc'][1] = str(geo['loc'][1])[:6]
            geo['radius'] = str(geo['radius'])[:7]
                
        output = template("listEvents",
                          geoEvents=geoEvents,
                          tagEvents=tagEvents)
    
    else:
        safeResponse = {'data':events, 'meta':200}
        output = json.dumps(safeResponse)
        
    return output
        
#------------------------------------------------------------------------------------------------

@route('/event')
def on_event_request():
    ''' Receives GET requests from the user to setup subscriptions. '''

    # Does the user want a linked outpage to make it easier to link to?
    htmlPage = bool(request.query.html)
    event = None
    
    tag    = request.query.tag
    lat, lon, radius = subscriptionWorker.checkGeos(request.query.lat, request.query.lon, request.query.radius)
    
    if tag and len(tag) > 0:
        event = {'object' : 'tag',
                 'tag'    :  tag.lower()}
    
    elif lat and lon and radius:
        
        # Convert the incoming metres radius to degrees
        latRad, lonRad = crowdedWorker.radialToLinearUnits(float(lat))
        scale = (latRad+lonRad)/2.0
        radius = float(radius)/scale
        
        event = {'object' : 'geography',
                 'lat'    : float(lat),
                 'lon'    : float(lon),
                 'radius' : float(radius)}    
    
    else:
        print 'Must specify a lat/lon/radius or tag.'
        redirect("/help")
        return
    
    if not event:
        response = {'success': False}
    # Get the response form updating the backend records
    else:
        response = subscriptionWorker.buildSubscription(event)
        
        # Now get something populated in that so that its not blank
        subInfo = [{"object" : response['object'], "object_id" : response['objectId']}]
        crowdedWorker.main(p, json.dumps(subInfo))
    
    # A user linked page for getting to the event splash page
    if response.has_key('url') and response['success']==True:
        if htmlPage == True:
            output = template("goToEventPage",
                              objectId=response['objectId'],
                              eventPage=response['url'],
                              helpPage=p.helpUrl)
        else:
            output = json.dumps(response)
    else:
        redirect("/help")
        
    return output

#-------------------------------------------------------------------------------------------

@route('/event_callback')
@post('/event_callback')
def on_event_callback():
    ''' The function that does both the subscription authorisation - a response to their server
        and receives the POST payload to get the update messages for building endpoint fetches'''
    
    # Challenge to be responded to - this allows subscriptions to be setup
    challenge = request.GET.get("hub.challenge")
    if challenge: 
        return challenge

    # If its a POST, get the payload
    try:
        raw_response = request.body.read()
    except:
        on_error(message='Failed on body read request.')
    
    # Make sure that the payload exists
    if raw_response == None:
        on_error(message='Failed on body read request.')
    else:
        crowdedWorker.main(p, raw_response)
    
#------------------------------------------------------------------------------------------------

@route('/test')
def test():
    ''' General GET test to see whether there are errors in this file '''
    f = open(os.path.join(cwd, 'test.txt'), 'a')
    f.write('writing out the test line from hitting this site.')
    f.close()
    return "Hello world - this worked"

#------------------------------------------------------------------------------------------------

@route('/static/<filepath:path>')
def server_static(filepath):
    ''' Route to serve up the static files'''
    #return static_file(filepath, root='/Users/brantinghamr/Documents/Code/eclipseWorkspace/crowded/dev/app/static/')
    return static_file(filepath, root=p.webStaticRoute)

#------------------------------------------------------------------------------------------------

@route('/help')
def helpPage():
    ''' Will eventually render some help. '''

    #output = template("help")    
    return "help coming soon."

#------------------------------------------------------------------------------------------------

@route('/noevent/<objectId>')
def noEvent(objectId=None):
    ''' Renders an error page of sorts saying that the event doesn't exist. '''

    output = template("noEvent", objectId=objectId, helpPage=p.helpUrl)    
    return output

#------------------------------------------------------------------------------------------------

@route('/events/<objectId>')
def eventSplash(objectId=None):
    ''' Renders the media that relates to this event out to the browser. '''

    if not objectId:
        redirect("/help")
        return

    # Get the objectId
    doc = crowdedWorker.getMediaByObjectId(p, objectId)
    if not doc or len(doc.keys())<1 or 'subType' not in doc.keys():
        redirect("/noevent/%s" %(objectId)) 
        return
    
    # Reorder the media by timestamp
    media = crowdedWorker.reorderMedia(doc['media'], 200)

    # Other web page elements
    header = 'Event Media...'
    
    # Get subheader
    if doc['subType']=='geography':
        loc = doc['loc']
        # Get the correct radius units
        # Convert the incoming metres radius to degrees
        latRad, lonRad = crowdedWorker.radialToLinearUnits(float(loc[1]))
        scale = (latRad+lonRad)/2.0
        radius = float(doc['radius'])*scale
        
        subHeader = 'Event Location: lat: %s, lon: %s, radius: %sm' %(loc[1], loc[0], radius)
    elif doc['subType']=='tag':
        subHeader = 'Event Tag: %s' %(objectId)

    # Filter the list down
    usefulTags = crowdedWorker.popUselessTags(p, doc['tags'])
    tags = crowdedWorker.filterTagsByCount(usefulTags, objectId, numberTopTags=15)
    associatedTags = 'Most commonly associated tags (count): '
    associatedTags += ', '.join(tags)
    
    # When the subscription was registered
    initiated = doc['start'].strftime('%H:%M:%SZ on %a %d %b %Y')

    # Push the arguments through the template and return the output
    output = template("renderMedia",
                      photos         = media,
                      header         = header,
                      subHeader      = subHeader,
                      associatedTags = associatedTags,
                      initiated      = initiated)
    
    return output
        
#------------------------------------------------------------------------------------------------

@route('/contribute', method='POST')
def contributePOST():
    ''' Takes in POST payload, checks it and then adds it to the relevant event doc. '''

    data = request.body.read()
    if not data:
        response = {'meta':400, 'reason':'no data provided'}
        return response
    
    mediaUpdates = json.loads(data)
    
    newMedia = {}
    # Loop to check the media being posted in
    for media in mediaUpdates['data']:
        valid, objectId, validMedia, tags = crowdedWorker.validMediaCheck(p, media)
        
        if valid == False:
            response = {'meta' : {'code':400}}
            return json.dumps(response)
        else:
            newMedia[str(objectId)] = validMedia
    
    # Loop to insert it into mongo
    for objectId in newMedia.keys():
        success = crowdedWorker.updateEventMedia(evCollHandle, objectId, newMedia[objectId], tags)
        if success == 0:
            response = {'meta'  : {'code':400}, 'reasons' : 'Failed to update media collection for object: %s' %(objectId)}
        else:
            response = {'meta' : {'code':200}}
    
