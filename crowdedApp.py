import os
import sys
import bottle
import json
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

from baseUtils import getConfigParameters
import crowdedWorker
import subscriptionWorker

bottle.debug(True)

#///////////////////////////////////////////////////////////////////////////////////////////////
#
# Bottle (python micro-framework) based web application for interacting with the instagram API.
# 
# A web server is needed for instagrams pubsubhubub - based API. It is needed for the setting up
# of subscriptions (this app responds to say that the subscription is authorised). It is also 
# needed to receive update POSTs from the Instgram Publisher. The updates are small json payloads
# that notify this app that something matching the subscription has changed. The updates do not
# contain the media or the media metadata. 
#
# This app, upon receipt of an update POST, passes the payload to igramSubscrption(.py) which
# reads the update and hits the relevant API search endpoint to retrieve the recently changed
# media metadata.
#
# This app doesn't include any calls for authorising other applications or users. It just handles
# the updates and subscription authorisation. An update payload looks like this:-
#
# [{"changed_aspect": "media", "subscription_id": 2229309, "object": "tag", "object_id": "olympics2012", "time": 1345065662}]
# 
# Note, its a list so you have multiple updates in a single payload - the code is written to handle that.
#
#
#///////////////////////////////////////////////////////////////////////////////////////////////

os.chdir('/home/dotcloud/current/')
cwd = os.getcwd()
cfgs = os.path.join(cwd, 'config/crowded.cfg')
p = getConfigParameters(cfgs)

#------------------------------------------------------------------------------------------------

def on_error(errFile='errors.txt', message=None):
    ''' Handles an error message '''
    
    f = open(os.path.join(cwd, errFile), 'a')
    f.write(message + '\n')
    f.close()

#------------------------------------------------------------------------------------------------

@route('/event')
def on_event_request():
    ''' Receives GET requests from the user to setup subscriptions. '''

    # Does the user want a linked outpage to make it easier to link to?
    htmlPage = bool(request.query.html)
    print htmlPage
    
    event = None
    
    tag    = request.query.tag
    lat, lon, radius = subscriptionWorker.checkGeos(request.query.lat, request.query.lon, request.query.radius)
    
    print "Tag", tag
    print lat, lon, radius
    
    if tag and len(tag) > 0:
        event = {'object' : 'tag',
                 'tag'    :  tag.lower()}
    
    elif lat and lon and radius:
        event = {'object' : 'geography',
                 'lat' : float(lat),
                 'lon' : float(lon),
                 'radius' : float(radius)}    
    
    else:
        abort(400, 'Must specify tag OR lat & lon & radius.')

    
    if not event:
        abort(400, 'Failed to build event for subscription worker.')
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
    if not doc or len(doc.keys())<1:
        redirect("/noevent/%s" %(objectId)) 
        return
    
    media = crowdedWorker.reorderMedia(doc['media'])

    # Other web page elements
    header = 'Event Media...'
    
    # Get subheader
    if doc['subType']=='geography':
        loc = doc['loc']
        subHeader = 'Event Location: lat: %s, lon: %s, radius: %skm' %(loc[1], loc[0], doc['radius']/1000.)
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
    
    """
    SUCCESSFULLY CREATED A TAG SUBSCRIPTION
    NEED TO CHECK THE GEO SUBSCRIPTION - DOES THAT WORK OK? - print statements in the @route above to check this
    comment this, then re-push.
    NEED TO CHECK THE DELETING OF SUBSCRIPTIONS USING THE CLEANUP FUNCTIONS
    NEED TO SEE WHETHER SUBSCRIPTION UPDATES ARE COMING INTO THE MONGO
    NEED TO CHECK WHETHER THE INTERFACE IS WORKING CORRECTLY
    """
    
    