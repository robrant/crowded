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

from baseUtils import getConfigParameters
from instagram import InstagramAPI

#------------------------------------------------------------------------------------------------------------

def main(configFile=None):
    ''' Deletes all subscriptions from the Instagram server. Typically called
        on a new dotcloud push just to make sure its all clear.'''

    # Get the config information into a single object
    p = getConfigParameters(configFile)
    
        # Get the client and secret keys
    api = InstagramAPI(client_id=p.client, client_secret=p.secret)
    
    # Get all current subs
    subs = api.list_subscriptions()

    # For each active sub, delete it
    if subs['meta']['code'] == 200:
        
        for sub in subs['data']:
            
            if sub['type'] == 'subscription':
                deleted = api.delete_subscriptions(id=int(sub['id']))
        
        # Final check - make sure they're definitely all gone
        subs = api.list_subscriptions()
        if len(subs['data']) == 0:
            success = True
        else:
            success = False
    
    else:
        success = False

if __name__ == "__main__":
    
    configFile = sys.argv[1]

    main(configFile)