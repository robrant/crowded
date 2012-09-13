import sys

from pymongo import Connection
from pymongo.errors import ConnectionFailure
from pymongo import GEO2D, ASCENDING, DESCENDING

def getHandle(host='localhost', port=27017, db='bam', user=None, password=None):
    ''' Acquires a mongo database handle or handles the exception'''
    
    # Establish the connection
    try:
        c = Connection(host=host, port=port)
    except ConnectionFailure, e:
        sys.stderr.write("Could not connect to Mongodb: %s " % e)
        sys.exit(1)
    
    # Get a database handle
    dbh = c[db]
    assert dbh.connection == c

    if user and password: 
        try:
            auth = dbh.authenticate(user, password)
        except Exception, e:
            sys.stderr.write("**** Failed to authenticate with mongo db. %s **** \n" % e)

    return c, dbh

#------------------------------------------------------------------------

def close(connection, dbHandle):
    ''' Handles the proper closing of the connection.'''
    
    connection.disconnect()
    
    return connection

#------------------------------------------------------------------------

def setupCollections(dbh, dbName='bam', dropCollections=None):
    
    ''' Sets up the database and its constituent elements. '''
    
    # Set up each of the collections
    #collections = ['keywords', 'baseline', 'timeseries', 'summary', 'thresholds', 'mapping', 'alerts']
    collections = ['baseline', 'timeseries', 'mapping', 'alerts']

    # Create each of the collections
    for coll in collections:
        if dropCollections:
            dbh.drop_collection(coll)
        # Create the collections
        try:
            dbh.create_collection(coll)
        except:
            print 'Failed to create the collection %s.' %(coll)
    
    return dbh

#------------------------------------------------------------------------
            
def setupIndexes(dbh, dbName='bam', dropIndexes=None):
    ''' Sets up the indexes on the collections '''
    

    
    # SUMMARY: Creates a unique index on the summary collection 
    if dropIndexes:
        dbh.baseline.drop_indexes()
        
    dbh.baseline.create_index([("mgrs",         DESCENDING),
                              ("keyword",       ASCENDING)],
                              unique  = True)
    
    # ALERTS: Creates a spatial index on the geos
    if dropIndexes:
        dbh.alerts.drop_indexes()
    
    dbh.alerts.create_index([("geo",    GEO2D),
                             ("keyword",ASCENDING),
                             ("start",  DESCENDING)],
                            name = 'alerts_geo_kw_start_idx')

    # TIMESERIES: Create index on start and keyword
    if dropIndexes:
        dbh.timeseries.drop_indexes()

    # Create a sparse index on 'blank' field.
    #dbh.timeseries.create_index(...SPARSE...)

    dbh.timeseries.create_index([("mgrs",           ASCENDING),
                                 ("keyword",        ASCENDING)])
        
    dbh.timeseries.create_index([("start",          DESCENDING),
                                 ("keyword",        ASCENDING)])
    
    dbh.timeseries.create_index([("start",          DESCENDING),
                                 ("keyword",        ASCENDING),
                                 ("mgrs",           ASCENDING)])
    
    dbh.timeseries.create_index([("start",          DESCENDING),
                                 ("keyword",        ASCENDING),
                                 ("mgrs",           ASCENDING),
                                 ("mgrs_precision", ASCENDING)])
    
    #dbh.timeseries.create_index([("start",          DESCENDING)])

    
    return dbh
    
# Get connection to mongo
