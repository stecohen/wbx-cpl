#!/usr/local/bin/python

import requests
import os
import json
import logging
import time
import re      
import datetime
import importlib.metadata
import inspect
import pandas as pd 
pd.set_option('display.max_colwidth', 80)
import click
from pprint import pprint

import wbx_cpl.utils
import wbx_cpl.msgsData
import wbx_cpl.wbx

ut=wbx_cpl.utils.UtilsTrc()
wbxr=wbx_cpl.wbx.WbxRequest(ut)

if ( 'AUTH_BEARER' in os.environ ):
    wbxr.set_token( os.environ['AUTH_BEARER'] )

__version__ = my_name = "N/A"
try:
    __version__ = importlib.metadata.version(__package__)
    my_name = __package__
except:
    print("Local run")

logging.basicConfig()

NOW = datetime.datetime.now()
UTCNOW = NOW.isoformat(timespec='milliseconds') + 'Z'

###################
### UTILS functions 
###################

# print items array fields listed in 'il' 
#
def print_items(il, items):
    for i in il:
        print(i,",", end='', sep='')
    print ("")        
    for item in items:
        for i in il:
            try:
                v=item[i]
            except KeyError:
                v=""
            print (v, ",", end='', sep='')
        print ("")
    
###############
## Comp Officer stuff 
################

# extracts file name from content disposition header field 
def extract_file_name(cd):
    name=re.findall('filename="(.+)"', cd)[0]
    return(name)
    
class msgsDF:

    cols_user = {'id':[], 'created':[], 'text':[], 'fileCount':[],'files':[], 'fileNames':[], 'roomType':[], 'roomId':[]}
    cols_space = {'id':[],'sentBy':[],'created':[], 'text':[], 'fileCount':[],'files':[], 'fileNames':[]}
    
    def __init__(self, add_title=False, IsSpace=False):
        mycols=self.cols_user
        if IsSpace:
            mycols=self.cols_space
        if  add_title:
            mycols['title']=[]
        self.df = pd.DataFrame(mycols)
        
    def add_msgs(self, ue, cr_msgs, dl_msgs, add_title=False, IsSpace=False):

        mycols=self.cols_user
        if IsSpace:
            mycols=self.cols_space
        #
        # error protection 
        if 'items' not in cr_msgs:
            ut.trace (2, f"no messages in " + str(msg))
            return
        
        #
        # iterate deleted messages and store in dl_msgs_d
        dl_msgs_d={}
        if 'items' in dl_msgs:
            for item in dl_msgs['items']:
                msg=item['data']
                dl_msgs_d[msg['id']]=msg

        #
        # iterate created messages
        for item in cr_msgs['items']:
            msg=item['data']
            title="N/A"
            ut.trace (3, f"got message: " + str(msg))
            #
            # new row from msg
            new_row={}
            for i in mycols:
                if i in msg:
                    new_row[i]=msg[i]

            # add deleted date info
            #
            new_row['deleted']='N'
            if dl_msgs_d.get(new_row['id']):
                new_row['deleted']='Y'

            #
            # add sender         
            new_row['sentBy']=ue
            #
            # process 'files' column : add 'fileCount' and 'fileNames' values
            file_count=0
            file_list=[]
            if ('files' in msg):
                file_count = len(msg['files'])
                fileURLs=msg['files']
                for furl in fileURLs:
                    ut.trace(3, f"processing {furl}")
                    # read headers
                    hds=wbxr.req_head(furl)
                    if 'content-disposition' in hds:
                        fn=extract_file_name(hds['content-disposition'])
                        file_list.append(fn)
                    else:
                        ut.trace(3, f"could not find 'content-disposition' header in {furl}")
                new_row['fileNames']=file_list
                ut.trace(3, f"got {new_row['fileNames']}")
            new_row['fileCount'] = int(file_count)
            #
            # add column 'title' if long process option 
            if ( add_title ):
                if 'roomId' in msg:
                    # direct rooms don't have a title. Need to extract the 'other' member in the space
                    if (msg['roomType'] == 'direct'):
                        ut.trace (3, "direct message, getting other person email " + str(locals()))
                        other_member=get_other_person_membership(msg['roomId'],msg['personId'])
                        # title=f"{other_member['personDisplayName']} ({other_member['personEmail']})"
                        title=f"{other_member['personEmail']}"
                    else:
                        room=wbxr.get_wbx_data(f"rooms/{msg['roomId']}","")
                        if ('title' in room) :
                            title=room['title']
                    new_row['title']=title
            #
            # finally add to DF  
            if ('created' in msg):
                self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
            #
        return(self.df)
  

class recordingsDF:

    cols = {'id':[],'topic':[],'createTime':[], 'hostEmail':[], 'playbackUrl':[],'durationSeconds':[], 'playbackUrl':[]}
    
    def __init__(self):
        mycols=self.cols
        self.df = pd.DataFrame(mycols)
        
    def add_recs(self, recordings):
        mycols=self.cols
        #
        # error protection 
        if 'items' not in recordings:
            ut.trace (2, f"no recordings in " + str(recordings))
            return
        #
        # iterate recordings 
        for rec in recordings['items']:
            ut.trace (3, f"got rec: " + str(rec))
            # new row 
            new_row={}
            for i in mycols:
                if i in rec:
                    new_row[i]=rec[i]
            # store in DF
            self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        # return DF
        return(self.df)
  

# get the 'other' (apart from given 'uid') person membership in a direct 1:1 space
# 
def get_other_person_membership(roomId, uid):
    ut.trace(3, f"{roomId} {uid} ")
    members=wbxr.get_space_memberships(roomId, True)
    ut.trace(3, f"got {members}")
    if 'items' in members:
        for item in members['items']:
            if (item['id'] != uid):
                return(item)
    return({})

# returns created and deleted messages objs for given user email 
# optional parameters passed as json string like '{"max":1000}'
# returns empty obj if not found
# 
def get_user_msgs(ue, user_opts=""):

    uid = wbxr.get_user_id(ue, True)
    frm = datetime.datetime.now() - datetime.timedelta(30)
    utcFrm=frm.isoformat(timespec='milliseconds') + 'Z'
    to = UTCNOW
    opts = {'max': 100,'from':utcFrm,'to':to}

    if (uid):
        # override default options w/ user options
        #
        if (user_opts):
            try:
                userOpts=json.loads(user_opts)
                if ( userOpts.get('from') or userOpts.get('to') ) : # erase time defaults 
                    opts = {'max': 100}
                for k in userOpts:
                    opts[k]=userOpts[k]
            except:
                ut.trace(1, f"error parsing {user_opts} not a valid JSON format")

        # construct url parameter string
        #
        params=f"?resource=messages&actorId={uid}&"
        for k in opts:
            params=f"{params}&{k}={opts[k]}"
        ut.trace (3, f"searching created msgs params = {params}")
        created=wbxr.get_events(params)

        # now search for deleted messages so we can mark them as such
        #
        params=f"?resource=messages&actorId={uid}&type=deleted"
        for k in opts:
            params=f"{params}&{k}={opts[k]}"
        ut.trace (3, f"searching deleted msgs params = {params}")
        deleted=wbxr.get_events(params)

        return(created, deleted)

    else:
        ut.trace(1, f"cannot find user {ue}")
        return({})

# print panda DF from list of messages
# pull msg info in csv fmt  
# 
def print_user_msgs(df, csvdest):
    #
    # print to screen and file if option on 
    df = df.astype({'fileCount': 'int'})
    print(df.loc[:, ~df.columns.isin(['sentBy', 'id','files', 'roomId', 'fileNames'])])
    if csvdest:
        df.to_csv(csvdest, index=False)
        ut.trace(2, f"{csvdest} written.")

# print to screen and file if option on 
#
def print_space_msgs(df, csvdest):
    df = df.astype({'fileCount': 'int'})
    df = df.sort_values(by=['created'])
    print(df.loc[:, ~df.columns.isin(['id', 'files', 'fileNames'])])
    if csvdest:
        df.to_csv(csvdest, index=False)
        ut.trace(2, f"{csvdest} written.")


# print to screen and file if option on 
#
def print_recordings(df, csvdest):
    df = df.sort_values(by=['createTime'])
    print(df.loc[:, ~df.columns.isin(['playbackUrl'])])
    if csvdest:
        df.to_csv(csvdest, index=False)
        ut.trace(2, f"{csvdest} written.")


# pull membership info in csv fmt  
# 
def extract_membership_csv(members, csvFile):
    #
    cols = {'personEmail':[],'personDisplayName':[],'created':[]}
    df=pd.DataFrame(cols)
    if 'items' in members:
        for mbr in members['items']:
            new_row={}
            for f in cols:
                if f in mbr:
                    new_row[f]=mbr[f]
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        print(df.loc[:, ~df.columns.isin(['id','files', 'roomId'])])
        csvFile and df.to_csv(csvFile, index=False)
    else:
        ut.trace(3, f"no membership data")  


#####################
### User commands ###
#####################

# user facing top level fct 
# get messages for given user email 
# optional parameters passed as json string like '{"max":1000}'
# 
@click.command()
@click.option('-f', '--filter', help='JSON string to filter events search e.g. {"from":"2023-12-31T00:00:00.000Z", "max":1}.')
@click.option('-t', '--title', is_flag=True, show_default=True, default=False, help='Add room title column (requires additonal processing).')
@click.option('-c', '--csvfile', help='Save results to CSV file.')
@click.argument('email')
def user_messages(email, title, filter, csvfile):
    """List (up to 1000) messages sent by given user email. Use the filter option to limit the search if needed."""
    #
    # initialise pandas data frame 
    msgdf=msgsDF(title, False)
    if filter :
        try:
            optsJ=json.loads(filter)
        except:
            ut.trace(1, f"error {filter} not in valid JSON format")
            return(-1)
    # get data   
    ut.trace(3, f"got params {email} {filter}")
    (c,d)=get_user_msgs(email, filter)
    if c:
        df=msgdf.add_msgs(email, c, d, title, False)
        print_user_msgs(df, csvfile)
    else:
        ut.trace(2, "No messages from {email}")


@click.command()
@click.argument('spaceId')
@click.option('-f', '--filter', help='JSON string to filter events search e.g. {"from":"2023-12-31T00:00:00.000Z", "max":1}.')
@click.option('-c', '--csvfile', help='Save results to CSV file.')
def space_messages(spaceid, filter, csvfile):
    """List messages in given space ID. Limited to 1000 per user."""
    #
    # init
    ut.trace(3, locals())
    if filter :
        try:
            optsJ=json.loads(filter)
        except:
            ut.trace(1, f"error {filter} not in valid JSON format")
            return(-1) 
    # init
    msgdf=msgsDF(False, True) # msgs DF

    # get list of users in space, extract their msgs, store in panda DF
    #
    members=wbxr.get_space_memberships(spaceid)
    if 'items' in members:
        for user in members['items']:
            ue=user['personEmail']
            uid = wbxr.get_user_id(ue)
            ut.trace(3, f"processing user {ue}")
            if (uid):
                (c, d)=get_user_msgs(ue, filter)
                df=msgdf.add_msgs(ue, c, d, False, True)
            else:
                ut.trace(3, f"{ue} not found")
        # print
        print_space_msgs(df, csvfile)
    else:
        ut.trace(3, f"no membership data for {spaceid}")


# user facing top level fct 
# get memberships for given room id 
# 
@click.command()
@click.argument('spaceId') 
@click.option('-c', '--csvfile', help='Save results to CSV file.')
def space_members(spaceid, csvfile):
    """List emails of members in given space ID."""
    data = wbxr.get_space_memberships(spaceid)
    extract_membership_csv(data, csvfile)

# download files in given msg id   
#
@click.command()
@click.argument('msgId') 
@click.option('-d', '--dir', default="", help='directory name to downlaad to.')
def download_msg_files(msgid, dir):
    """Download files attached to given message ID. Files will be downloaded in current directoty by default."""
    msg = wbxr.get_wbx_data(f"messages/{msgid}")
    if 'files' in msg:
        files=msg['files']
        for f in files:
            wbxr.download_contents(f, dir)
    else:
        ut.trace(1, f"no attachments found in msg {msgid}")


# list recordings  
#
@click.command()
@click.argument('site') 
@click.option('-c', '--csvfile', help='Save results to CSV file.')
@click.option('-f', '--filter', help='JSON string to filter events search e.g. {"from":"2023-12-31T00:00:00.000Z", "max":1}.')
def recordings(site, csvfile, filter):
    """List recordings for given webex site"""
    #
    # defaults options
    #
    frm = datetime.datetime.now() - datetime.timedelta(30)
    utcFrm=frm.isoformat(timespec='milliseconds') + 'Z'
    to = UTCNOW
    opts = {'max': 100,'from':utcFrm,'to':to}

    # override default options w/ user options
    #
    if (filter):
        try:
            userOpts=json.loads(filter)
            if ( userOpts.get('from') or userOpts.get('to') ) : # erase time defaults 
                opts = {'max': 100}
            for k in userOpts:
                opts[k]=userOpts[k]
        except:
            ut.trace(1, f"error parsing {filter} not a valid JSON format")
        

    
    # construct url parameter string
    #
    params=f"siteUrl={site}"
    for k in opts:
        params=f"{params}&{k}={opts[k]}"

    # get recording data
    #
    data = wbxr.get_wbx_data(f"admin/recordings?{params}")

    # store in panda DF and print
    #
    df=recordingsDF()
    items=data.get('items')
    if (items):
        df=df.add_recs(data)
        print_recordings(df, csvfile)
    else:
        ut.trace(1, f"no recordings found.")


# get recording details
#
@click.command()
@click.argument('id') 
def recording_details(id):
    """Print detais of given recording ID."""
    data = wbxr.get_wbx_data(f"recordings/{id}")
    pprint(data, depth=2, indent=4)
    

@click.group()
@click.version_option(__version__)
@click.option('-t', '--token', help='Your access token. AUTH_BEARER env variable by default. You can find your personal token at https://developer.webex.com/docs/getting-started.')
@click.option('-d', '--debug', default=2, help='Debug level.')
def cli(debug, token):
    ut.setDebugLevel(debug)
    if (debug >=3 ):
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
    if (token):
        wbxr.set_token( token )


cli.add_command(download_msg_files)
cli.add_command(space_messages) 
cli.add_command(user_messages) 
cli.add_command(space_members) 
cli.add_command(recordings) 
cli.add_command(recording_details)

if __name__ == '__main__':
    cli()