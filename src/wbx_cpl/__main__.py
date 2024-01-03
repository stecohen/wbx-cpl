#!/usr/local/bin/python

import csv
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
UTCNOW = NOW.isoformat() + 'Z'

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
        
    def add_msgs(self, ue, msgs, add_title=False, IsSpace=False):

        mycols=self.cols_user
        if IsSpace:
            mycols=self.cols_space
        #
        # iterate messages
        for item in msgs['items']:
            msg=item['data']
            title="N/A"
            ut.trace (3, f"got message: " + str(msg))
            #
            # new row from msg
            new_row={}
            for i in mycols:
                if i in msg:
                    new_row[i]=msg[i]
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

# get messages obj for given user email 
# optional parameters passed as json string like '{"max":1000}'
# returns empty obj if not found
# 
def get_user_msgs(ue, user_opts=""):

    uid = wbxr.get_user_id(ue, True)
    frm = datetime.datetime.now() - datetime.timedelta(30)
    utcFrm=frm.isoformat() + 'Z'
    to = UTCNOW
    opts = {'max': 100,'from':utcFrm,'to':to}

    if (uid):
        # override default options w/ user options
        #
        if (user_opts):
            try:
                userOpts=json.loads(user_opts)
                for k in userOpts:
                    opts[k]=userOpts[k]
            except:
                ut.trace(1, f"error parsing {user_opts} not a valid JSON format")

        # construct url parameter string
        #
        params=f"?resource=messages&actorId={uid}"
        for k in opts:
            params=f"{params}&{k}={opts[k]}"
        ut.trace (3, f"params = {params}")
        d=wbxr.get_events(params)
        return(d)

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
    print(df.loc[:, ~df.columns.isin(['id', 'files', 'fileNames'])])
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
@click.option('-f', '--filter', help='json string for filtering events search. Eg "max":1')
@click.option('-t', '--title', is_flag=True, show_default=True, default=False, help='Adds room title column (requires additonal processing)')
@click.option('-c', '--csvdest', help='save results to CSV file')
@click.argument('email')
def user_messages(email, title, filter, csvdest):
    """List messages sent by given user email, up to 1000 messages. """
    
    # initialise pandas data frame 
    msgdf=msgsDF(title, False)
    if filter :
        try:
            optsJ=json.loads(filter)
        except:
            ut.trace(1, f"error {filter} not in valid JSON format")
            return(-1)
        
    ut.trace(3, f"got params {email}. Calling get_user_msgs {email} {filter}")
    d=get_user_msgs(email, filter)
    if d:
        df=msgdf.add_msgs(email, d, title, False)
        print_user_msgs(df, csvdest)

@click.command()
@click.argument('spaceId')
@click.option('-f', '--filter', help='json string for filtering events search for each user. Eg {"max":1}')
@click.option('-c', '--csvdest', help='destination file name')
def space_messages(spaceid, filter, csvdest):
    """list messages in given space id """
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
                msgs=get_user_msgs(ue, filter)
                ut.trace(3, f"got {str(msgs)[:100]}...")
                df=msgdf.add_msgs(ue, msgs, False, True)
            else:
                ut.trace(3, f"{ue} not found")
        # print
        print_space_msgs(df, csvdest)
    else:
        ut.trace(3, f"no membership data for {spaceid}")


# user facing top level fct 
# get memberships for given room id 
# 
@click.command()
@click.argument('spaceId') 
@click.option('-c', '--csvFile', help='CSV file destination.')
def space_members(spaceid, csvfile):
    """List emails of members in given space ID"""
    data = wbxr.get_space_memberships(spaceid)
    extract_membership_csv(data, csvfile)

# download files in given msg id   
#
@click.command()
@click.argument('msgId') 
def download_msg_files(msgid):
    """Download files attached to given message ID"""
    msg = wbxr.get_wbx_data(f"messages/{msgid}")
    if 'files' in msg:
        files=msg['files']
        for f in files:
            wbxr.download_contents(f)
    else:
        ut.trace(1, f"no attachments found in msg {msgid}")

@click.group()
@click.version_option(__version__)
@click.option('-t', '--token', help='Your access token. Read from AUTH_BEARER env variable by default.')
@click.option('-d', '--debug', default=2, help='debug level.')
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

if __name__ == '__main__':
    cli()