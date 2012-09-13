crowded
-----------

A crowd sourced view of events as they happen.

Description:
------------
Crowded collates images from a range of sources based on a request for information
about a location or tag. The primary method of calling is a webservice which in theory
could be made in response to anything. It is intended to be event driven, where the
events are detected by other processors outside this app.

How it works:
-------------
On receipt of a correctly formatted GET (should probably be a PUT/POST),
the server registers an event in mongo. That event is used to frequently search for other
media was either in the same spatial proximity or that shared the same tag/hashtag.


In the case of the instagram source and their pubsubhubub API, the receipt of a event
request also generates a subscription call to the instagram server. A subscription is
now setup for that event (tag or geo). crowded listens for the mediametadata from instagram
and stores the url to the images (along with some other info) within the event.  

Subscriptions will only be built based on tag or geolocation arguments at this point
The initialising call is made over https. In future, an oAuth key will be accepted as
an argument to ensure my client key isn't creating too many calls per hour.

The Query:
---------

/event?
tag=<tag to be subscribed to>
lat=<lat of the event of interest>
lon=<lon of the event of interest>
radius=<radius of the circle of interest - defaults to 1km >
Must have either tag OR lat/lon/radius

The response
------------
The response to the event request is the place id
or the tag and the url that can be hit to see the output page.

Front End
---------
The front end will render the current crowd-sourced images based on a
specific tag or the place. And indeed multiple combinations of
both tag and place. 


TODO:
-----
   
1. Submit a query to the instagram API as soon as the event is registered
   to backfill the photo content.
   
2. Check whether a URL is already in the urls list for instagram, flickr
   and panoramio. Not so relevant for the cameras. 
   
3. Build a simple API
   a. Respond with object id to the initial event build - this ensures the user knows the object.
   b. When queried for that object id, return a json object containing (option):-
      1. The dictionary of tag and count, object ID, lat, lon, radius
      2. The list of photo dictionaries (including the different resolutions) along with tag/objectid/llr.
    
4. Build a front page


 Collections
 -----------
 subs - stores metadata about active subscriptions. Docs = {sub_id  : 2049566,
 															start   : 2011-01-01T00:00:00,
 															protect : boolean}
 		with protect being a flag to say whether a subscription only gets blasted manually.
 		Might think about keeping URL call tallies in here too
 		
 events - stores information about the event of interest and the urls that
 		  relate to the activity. And any other tags that have also featured in the records.	
 														