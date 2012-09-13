import sys
import os
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
from pymongo import DESCENDING, ASCENDING, GEO2D
from baseUtils import getConfigParameters, handleErrors

#------------------------------------------------------------------------

def buildIndexes(p, collection, collHandle):
    ''' Build the indexes specified'''
   
    # Create indexes
    try:    
        if p.verbose==True:
            print "---- Create Plain Indexes."
        
        for index in collection['plain']:
            collHandle.create_index([(index, ASCENDING)])
            if p.verbose==True:
                print "---- Index Created On: %s." %index

    except Exception, e:
        handleErrors(p, e)

    # Create compound indexes
    try:
        if p.verbose==True:
            print "---- Create Compound Indexes."
    
        for index in collection['compound']:
            ## ********* NEED SOME CONTENT IN HERE **********
            if p.verbose==True:
                print "---- Index Created On: %s." %index

    except Exception, e:
        handleErrors(p, e)

    # Create compound indexes
    try:
        if p.verbose==True:
            print "---- Create Geo Indexes."
    
        collHandle.create_index([(collection['geo'], GEO2D)])
        if p.verbose==True:
            print "---- Index Created On: %s." %index

    except Exception, e:
        handleErrors(p, e)

#------------------------------------------------------------------------

def buildCollection(dbh, p, collectionName):
    ''' Build the collection specified'''

    # Create the collection
    try:
        if p.dropCollection==True:
            if p.verbose==True: print "---- Dropping Collection."
            print "---- Creating Collection."
            dbh.drop_collection(collectionName)
        dbh.create_collection(collectionName)
    except Exception, e:
        handleErrors(p, e)

    # Collection handle
    collHandle = dbh[collectionName]
    
    return collHandle
    
#------------------------------------------------------------------------

def main(configFile=None):
    ''' Builds the collections and indexes needed. '''

    # Get the config information into a single object
    p = getConfigParameters(configFile)

    # Get a db handle
    if p.verbose==True:
        print "---- Geting Mongo Handle."
    c, dbh = mdb.getHandle(host=p.dbHost, port=p.dbPort, db=p.db, user=p.dbUser, password=p.dbPassword)

    # The collections provided and create them and their indexes
    for coll in p.collections:
        collHandle = buildCollection(dbh, p, coll['collection'])
        indexes = buildIndexes(p, coll, collHandle)
    
    mdb.close(c, dbh)
    
if __name__ == "__main__":
    main()