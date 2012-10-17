import os
import mdb
import ConfigParser
import json
import logging

# Get the directory in which this was executed (current working dir)
cwd = os.getcwd()
wsDir = os.path.dirname(cwd)


class getConfigParameters():
    ''' Gets the configuration parameters into an object '''
    
    def __init__(self, filePath):
        
        config = ConfigParser.ConfigParser()
        try:
            config.read(filePath)
        except:
            logging.warning('Failed to read config file.')
        
        # Keep the location of the config file in the config file for mods on the fly
        self.configFile = filePath
        cwd = os.path.dirname(filePath)
        parent = os.path.dirname(cwd)
                
        # Mongo parameters
        self.dbHost     = config.get("backend", "host")
        self.dbPort     = config.getint("backend", "port")
        self.db         = config.get("backend", "db")

        self.dbUser         = config.get("backend", "user")
        self.dbPassword     = config.get("backend", "password")
        
        # Collections and indexes
        self.collections        = json.loads(config.get("backend", "collections"))
        self.subsCollection     = self.collections[1]['collection']
        self.eventsCollection   = self.collections[0]['collection']
        self.dropCollection = config.getboolean("backend", "drop_collection")

        # The fields that get checked to ensure valid POSTs for new media
        flds = json.loads(config.get("backend", "flds"))
        self.mediaFlds = flds['mediaFlds']

        # Parameters for the instagram API
        self.client = config.get("source", "client")
        self.secret = config.get("source", "secret")

        # URLs that get used
        self.geoUrl      = config.get("source", "geoUrl")
        self.tagUrl      = config.get("source", "tagUrl")

        self.subBaseUrl     = config.get("web", "subBaseUrl")
        self.baseUrl        = config.get("web", "baseUrl")
        self.helpUrl        = config.get("web", "helpUrl")
        self.webStaticRoute = config.get("web", "webStaticRoute")
        
        # Error Logging
        self.logLevel  = self.checkLogLevel(config.get("error", "loglevel"))
        errorPath      = config.get("error", "err_path")   
        self.errorPath = os.path.join(parent, errorPath)
        self.errorFile = config.get("error", "err_file")
        
        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        # TFL DATASET PARAMETERS
        try:    self.tflUrl = config.get("other_data", "tflUrl")
        except: self.tflUrl = None
        
        # VIEWFINDER DATASET PARAMETERS
        try:    self.viewFinderUrl = config.get("other_data", "vfUrl")
        except: self.viewFinderUrl = None

        # SOCIALISE DATASET PARAMETERS
        try:     self.socialiseUrl = config.get("other_data", "seUrl")
        except:  self.socialiseUrl = None

        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

    def checkLogLevel(self, logLevel):
        ''' Checks that the log level is correct or defaults to DEBUG.'''
        
        logLevel = logLevel.upper()
        if logLevel in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            level = getattr(logging, logLevel)
        else:
            level = 10
        return level
        
#----------------------------------------------------------------------------------------

def getMongoHandles(p):
    ''' Gets the mongo connection handle, authentication and the collection handle.  '''

    # Handles the mongo connections
    c, dbh = mdb.getHandle(db=p.db, host=p.dbHost, port=p.dbPort)

    # Authentication
    try:
        auth = dbh.authenticate(p.dbUser, p.dbPassword)
    except Exception, e:
        print "Failed to authenticate with mongo db."
        print e

    collHandle = dbh[p.slangCollection]
    emoCollHandle = dbh[p.emoCollection]
    
    return c, dbh, collHandle, emoCollHandle

#----------------------------------------------------------------------------------------

def decodeEncode(token, encoding='latin-1'):
    ''' Holds it all together '''
    
    token = token.decode(encoding)
    token = token.encode('utf8')
    
    return token    
#-------------------------------------------------------------------------------------

