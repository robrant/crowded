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

import mdb
from pymongo import DESCENDING, ASCENDING, GEO2D
from baseUtils import getConfigParameters

#------------------------------------------------------------------------

def buildIndexes(p, collection, collHandle):
    ''' Build the indexes specified'''
    
    print "Building Indexes in here."
    # Create indexes
    try:    
        for index in collection['plain']:
            collHandle.create_index([(index, ASCENDING)])
            logging.info("---- Index Created On: %s." %index)
    except:
        logging.warning("INDEX CREATION FAILED.", exc_info=True)

    # Create compound indexes
    try:
        for index in collection['compound']:
            ## ********* NEED SOME CONTENT IN HERE **********
            logging.info("---- Index Created On: %s." %index)
    except:
        logging.warning("INDEX CREATION FAILED.", exc_info=True)

    # Create GEOSPATIAL indexes
    try:    
        collHandle.create_index([(collection['geo'], GEO2D)])
        logging.info("---- Geo Index Created")
    except:
        logging.warning("GEO INDEX CREATION FAILED.", exc_info=True)

#------------------------------------------------------------------------

def buildCollection(dbh, p, collectionName):
    ''' Build the collection specified'''

    # Create the collection
    try:
        if p.dropCollection==True:
            dbh.drop_collection(collectionName)
        dbh.create_collection(collectionName)
        logging.info("BUILDING COLLECTION: %s." %(collectionName))
    except:
        logging.warning("COLLECTION BUILD FAILED.", exc_info=True)

    # Collection handle
    collHandle = dbh[collectionName]
    
    return collHandle
    
#------------------------------------------------------------------------

def main(configFile=None):
    ''' Builds the collections and indexes needed. '''

    # Get the config information into a single object
    p = getConfigParameters(configFile)

    try:
        c, dbh = mdb.getHandle(host=p.dbHost, port=p.dbPort, db=p.db, user=p.dbUser, password=p.dbPassword)
    except:
        logging.warning("Failed to connect to db and get handle.", exc_info=True)

    # The collections provided and create them and their indexes
    for coll in p.collections:
        print "Building Collections and indexes: %s" %coll
        collHandle = buildCollection(dbh, p, coll['collection'])
        indexes = buildIndexes(p, coll, collHandle)
    
    mdb.close(c, dbh)
    
if __name__ == "__main__":
    main()