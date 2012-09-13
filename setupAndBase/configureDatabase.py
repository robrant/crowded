import sys
import os
import mdb
import json
from pymongo import DESCENDING, ASCENDING
from baseUtils import getConfigParameters, handleErrors

class params():
    
    def __init__(self, port, host, adminUser, adminPass):
        
        self.mongoPort = int(port)
        self.mongoHost = host
        self.adminUser = adminUser
        self.adminPass = adminPass

#------------------------------------------------------------------------------------

def writeConfigFile(configFile, dotcloudParams):
    ''' Writes in the new host and port information for the mongo instance.'''

    fIn = open(configFile, 'r')
    tmpFileName = os.path.join(os.path.dirname(configFile),'tmp.tmp')
    fOut = open(tmpFileName, 'w')
    
    for line in fIn:
        if line.startswith('port'):
            fOut.write('port = %s \n' %dotcloudParams.mongoPort)
        elif line.startswith('host'):
            fOut.write('host = %s \n' %dotcloudParams.mongoHost)
        else:
            fOut.write(line)
    fOut.close()
    fIn.close()
    
    os.rename(tmpFileName, configFile)

#------------------------------------------------------------------------------------

def getEnvironment(path='/home/dotcloud/', file='environment.json'):
    ''' Get the environment from the environment dotcloud file'''
    
    # Open the environment.json
    f = open(os.path.join(path, file), 'r')
    data = json.loads(f.read())
    f.close()
    
    # Get some of the environment parameters
    port = data['DOTCLOUD_DATA_MONGODB_PORT']
    host = data['DOTCLOUD_DATA_MONGODB_HOST']
    adminUser = data['DOTCLOUD_DATA_MONGODB_LOGIN']
    adminPass = data['DOTCLOUD_DATA_MONGODB_PASSWORD']
    
    p = params(port, host, adminUser, adminPass)

    return p

#------------------------------------------------------------------------

def main(configFile=None):
    ''' Takes the dotcloud default admin privs, authorises on the db, 
        creates the user I've specified and returns. '''
    
    # Get the parameters that were set up by dotcloud
    dcParams = getEnvironment()
    
    # Authenticate on the admin db
    c, dbh = mdb.getHandle(host=dcParams.mongoHost, port=dcParams.mongoPort, db='admin')

    # Authentication of the administrator
    try:
        auth = dbh.authenticate(dcParams.adminUser, dcParams.adminPass)
        print "---- Successful admin authorisation."
    except Exception, e:
        print "Failed to authenticate with mongo db as admin."
        print e

    # Create a new user
    p = getConfigParameters(configFile)
    # Switch the database handle to that being used from the admin one
    dbh = c[p.db]
    success = dbh.add_user(p.dbUser, p.dbPassword)
    
    try:
        auth = dbh.authenticate(p.dbUser, p.dbPassword)
        print "---- Successful user authentication."
    except Exception, e:
        print "Failed to authenticate with mongo db as user."
        print e
    
    # Write out the new information to the regular config file
    writeConfigFile(configFile, dcParams)
    
    mdb.close(c, dbh)
    
if __name__ == "__main__":

    # Command Line arguments
    configFile = sys.argv[1]
    
    # first argument is the config file path
    if not configFile:
        print 'no Config file provided. Exiting.'
        sys.exit()
    
    main(configFile)