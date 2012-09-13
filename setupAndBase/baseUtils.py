import os
import mdb
import ConfigParser
import json

# Get the directory in which this was executed (current working dir)
cwd = os.getcwd()
wsDir = os.path.dirname(cwd)


class getConfigParameters():
    ''' Gets the configuration parameters into an object '''
    
    def __init__(self, filePath):
        
        config = ConfigParser.ConfigParser()
        try:
            config.read(filePath)
        except Exception, e:
            print "Failed to read the config file for twitter connection client."
            print e
        
        # Keep the location of the config file in the config file for mods on the fly
        self.configFile = filePath
        
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
        self.verbose   = config.getboolean("error", "verbose")
        self.writeOut  = config.getboolean("error", "write_out") 
        errorPath      = config.get("error", "err_path")   
        self.errorPath = os.path.join(wsDir, errorPath)
        self.errorFile = config.get("error", "err_file")
        
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

#-------------------------------------------------------------------------------------

def handleErrors(p, error):
    ''' Handles the printing (or other) of errors. '''

    # Report out the parsing errors if verbose is set
    if p.verbose == True:
        print "-"*10+"Error"+"-"*10
        print error

    if p.writeOut == True:
        f = open(os.path.join(p.errorPath, p.errorFile), 'a')
        f.write(str(error)+'\n')
        f.close()
#----------------------------------------------------------------------------------------

def decodeEncode(token, encoding='latin-1'):
    ''' Holds it all together '''
    
    token = token.decode(encoding)
    token = token.encode('utf8')
    
    return token    
#-------------------------------------------------------------------------------------

