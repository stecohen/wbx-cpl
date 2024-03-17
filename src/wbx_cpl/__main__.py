#!/usr/local/bin/python

import requests
import os
import json
import logging
import time
import re      
import datetime
from datetime import timezone
import importlib.metadata
import inspect
import sys

import click
from pprint import pprint
import pandas

import wbx_cpl.utils as utils 
import wbx_cpl.dataframe as wbxdf
import wbx_cpl.wbx

ut=wbx_cpl.utils.UtilsTrc()
wbxr=wbx_cpl.wbx.WbxRequest()

__version__ = my_name = "N/A"
try:
    __version__ = importlib.metadata.version(__package__)
    my_name = __package__
except:
    print("Local run")

logging.basicConfig()

# move this to wbx.py
now = datetime.datetime.now(timezone.utc)
nowiso = now.isoformat(timespec='milliseconds')
UTCNOW = re.sub('\+.+','', nowiso) + 'Z' # remove the tz suffix 

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

# print panda DF from list of messages sent in meetings
# 
def print_in_meeting_user_msgs(df, csvdest, in_meeting=False):
    #
    # print to screen  
    if ( in_meeting ) :
        print(df.loc[:, ~df.columns.isin(['meetingId', 'id', 'fileCount' ])])
    else: 
        print(df.loc[:, ~df.columns.isin(['sentBy', 'id', 'fileCount' ])])
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
def print_memberships(members, csvFile):
    #
    cols = {'personEmail':[],'personDisplayName':[],'created':[]}
    df=wbxdf.membershipDF()
    df=df.add_data(members)
    print(df.loc[:, ~df.columns.isin(['id','files', 'roomId'])])
    csvFile and df.to_csv(csvFile, index=False)


#####################
### User          ###
#####################

@click.command()
@click.argument('email') 
def user_details(email):
    """Dispay user details."""
    data = wbxr.get_user_details(email)
    pprint(data)

@click.command()
def user_list():
    """List users ()"""
    df=wbxdf.usersDF()
    df.fetch_data()  # to do : add this as an opton
    df.list_users()

'''
@click.command()
def user_fetch_data():
    """Fetch user data from Webex."""
    df=wbxdf.usersDF()
    df.fetch_data()
'''

@click.group()
def user():
    pass

user.add_command(user_details, name='details')
# users.add_command(fetch_data)
user.add_command(user_list, name='list')

#####################
### Messages cmds ###
#####################

@click.command()
@click.option('-f', '--filter', help='JSON string to filter events search e.g. {"from":"2023-12-31T00:00:00.000Z", "max":1}.')
@click.option('-t', '--title', is_flag=True, show_default=True, default=False, help='Add room title column (requires additonal processing).')
@click.option('-c', '--csvfile', help='Save results to CSV file.')
@click.argument('email')
def user_messages(email, title, filter, csvfile):
    """List (up to 1000) messages sent by given user email. Use the filter option to limit the search if needed."""
    #
    # initialise pandas data frame 
    msgdf=wbxdf.msgsDF(type='user', title=title)
    if filter :
        try:
            optsJ=json.loads(filter)
        except:
            ut.trace(1, f"error {filter} not in valid JSON format")
            return(-1)
    # get data   
    ut.trace(3, f"got params {email} {filter}")
    (c,d)=wbxr.get_user_msgs(email, filter)
    if c:
        df=msgdf.add_msgs(email, c, d)
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
    msgdf=wbxdf.msgsDF('space') # msgs DF

    # get list of users in space, extract their msgs, store in panda DF
    #
    members=wbxr.get_space_memberships(spaceid)
    if 'items' in members:
        for user in members['items']:
            ue=user['personEmail']
            uid = wbxr.get_user_id(ue)
            ut.trace(3, f"processing user {ue}")
            if (uid):
                (c, d)=wbxr.get_user_msgs(ue, filter)
                df=msgdf.add_msgs(ue, c, d)
            else:
                ut.trace(3, f"{ue} not found")
        # print
        print_space_msgs(df, csvfile)
    else:
        ut.trace(3, f"no membership data for {spaceid}")


# get memberships for given room id 
# 
@click.command()
@click.argument('spaceId') 
@click.option('-c', '--csvfile', help='Save results to CSV file.')
def space_members(spaceid, csvfile):
    """List emails of members in given space ID."""
    data = wbxr.get_space_memberships(spaceid)
    print_memberships(data, csvfile)

# download files in given msg id   
#
@click.command()
@click.argument('msgId') 
@click.option('-d', '--dir', default="", help='directory name to downlaad to.')
def message_files(msgid, dir):
    """Download files attached to given message ID. Files will be downloaded in current directoty by default."""
    msg = wbxr.get_wbx_data(f"messages/{msgid}")
    if 'files' in msg:
        files=msg['files']
        for f in files:
            wbxr.download_contents(f, dir)
    else:
        ut.trace(1, f"no attachments found in msg {msgid}")


@click.group()
def messaging():
    pass

messaging.add_command(message_files)
messaging.add_command(space_messages) 
messaging.add_command(user_messages) 
messaging.add_command(space_members) 


#####################
### Recording     ###
#####################

@click.group()
def recording():
    pass

# list recordings  
#
@click.command()
@click.argument('site') 
@click.option('-c', '--csvfile', help='Save results to CSV file.')
@click.option('-f', '--filter', help='JSON string to filter search e.g. {"from":"2023-12-31T00:00:00.000Z", "max":1}. Same filters as https://developer.webex.com/docs/api/v1/recordings/list-recordings-for-an-admin-or-compliance-officer')
def recordings(site, csvfile, filter):
    """List recordings for given webex site"""
    #
    # defaults options
    #
    frm = datetime.datetime.now() - datetime.timedelta(30)
    utcFrm=frm.isoformat(timespec='milliseconds').replace('\+.*','') + 'Z'
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
    print(f"Serching recordings with parameters: {params}")
    data = wbxr.get_wbx_data(f"admin/recordings?{params}")

    # store in panda DF and print
    #
    df=wbxdf.recordingsDF()
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


# get recording content
#
@click.command()
@click.option('-d', '--dir', default="", help='directory destination for downlaads.')
@click.argument('id_or_csv') 
def get_recording_media(id_or_csv, dir):
    """downloads media of given recording ID or list of IDs in .CSV file (in the 'id' column). """
    iscsv = re.match('.*\.csv$', id_or_csv, re.IGNORECASE)
    if (iscsv):
        try:
            df = pandas.read_csv(id_or_csv)
            # print(df)
            for id in df['id']:
                print(f"Processing recording {id}...")
                data = wbxr.get_wbx_data(f"recordings/{id}")
                if ( data ) :
                    rdl=data['temporaryDirectDownloadLinks']['recordingDownloadLink']
                    wbxr.download_contents(rdl, dir, f"recording-{id}-{data['hostEmail']}-{data['createTime']}.{data['format']}")
                else :
                    ut.trace(2, f"No data for recording {id}")
        except FileNotFoundError:
            ut.trace(1, f"Error: File '{id_or_csv}' not found.")
            exit(-1)
        except Exception as e:
            ut.trace(1, f"An error occurred while reading the file '{id_or_csv}': {e}")
            exit(-1)
    else:
        data = wbxr.get_wbx_data(f"recordings/{id_or_csv}")
        if ( data ):
            rdl=data['temporaryDirectDownloadLinks']['recordingDownloadLink']
            wbxr.download_contents(rdl, dir, f"recording-{id_or_csv}-{data['hostEmail']}-{data['createTime']}.{data['format']}")
        else : 
            ut.trace(2, f"No data for recording {id_or_csv}")


recording.add_command(recordings, name='list') 
recording.add_command(recording_details, name='details')  
recording.add_command(get_recording_media, name='download')

#####################
### Meeting       ###
#####################

# WIP not needed I supposed
@click.command()
@click.option('-f', '--filter', help='JSON string to filter events search e.g. {"from":"2023-12-31T00:00:00.000Z", "max":1}.')
def fetch_meetings(filter):
    """Get raw meeting data from Webex."""
    
    # initialise pandas data frame 
    # 
    meetingsdf=wbxdf.meetingsDF()
    
    # proccess options
    #
    if filter :
        try:
            optsJ=json.loads(filter)
        except:
            ut.trace(1, f"error {filter} not in valid JSON format")
            return(-1)

    # get data   
    #
    meetingsdf.fetch_meetings()

# List meetings from events API
#
@click.command()
@click.option('-e', '--email', help='host email address. All users listed by default')
@click.option('-c', '--csvfile', help='Save results to CSV file.')
@click.option('-f', '--filter', help='JSON string to filter events search e.g. {"from":"2023-12-31T00:00:00.000Z", "max":1}.')
def list_meetings_events(email, csvfile, filter):
    """List past meetings events. Defaults to last 30 days and 100 meetings. 
    See filter option to override and https://developer.webex.com/docs/api/v1/events/list-events for details.""" 
    #
    meetingsdf=wbxdf.meetingsDF()
    # WIP meetingsdf.fetch_meetings() .... might do later to cache data in files
    meetingsdf.list_meetings(email, csvfile, filter)


@click.command()
@click.option('-f', '--filter', help='JSON string to filter events search e.g. {"from":"2023-12-31T00:00:00.000Z", "max":1}.')
@click.option('-t', '--title', is_flag=True, show_default=True, default=False, help='Add meeting title column (requires additonal processing).')
@click.option('-c', '--csvfile', help='Save results to CSV file.')
@click.argument('email')
def meeting_user_messages(email, title, filter, csvfile):
    """List messages sent in meetings by given user email. Use the filter option to limit the search if needed.
    Ths only applies to meetings hosted on the Webex Suite meeting platform."""
    #
    # initialise pandas data frame 
    msgdf=wbxdf.msgsDF('meeting')
    if filter :
        try:
            optsJ=json.loads(filter)
        except:
            ut.trace(1, f"error {filter} not in valid JSON format")
            return(-1)
    # get data   
    ut.trace(3, f"got params {email} {filter}")
    (c,d)=wbxr.get_user_msgs(email, filter, "meetingMessages")
    if c:
        df=msgdf.add_msgs(email, c, d)
        print_in_meeting_user_msgs(df, csvfile)
    else:
        ut.trace(2, f"No messages from {email}")

@click.command()
@click.argument('meetingid') 
@click.option('-c', '--csvfile', help='Save results to CSV file.')
def meeting_participants(meetingid, csvfile):
    """List meeting participants of given meeting ID."""
    dfm=wbxdf.meetingDF(meetingid)
    # dfm.add_participants(meetingid)
    dfm.print_participants(csvfile)

@click.command()
@click.argument('meetingid') 
def meeting_details(meetingid):
    """Details of given meeting ID."""
    dfm=wbxdf.meetingDF(meetingid)
    # dfm.get_details(meetingid)
    if ( dfm.details) :
        pprint(dfm.details)
    else :
        print("Error getting details of meeting ID {meetingid}")


@click.command()
@click.argument('meetingid') 
@click.option('-f', '--filter', help='JSON string to filter events search e.g. {"from":"2023-12-31T00:00:00.000Z", "max":1}.')
@click.option('-c', '--csvfile', help='Save results to CSV file.')
def meeting_messages(meetingid, filter, csvfile):
    """List messages posted in meeting ID, up to 100 messages per participant"""
    # init message DF
    msgdf=wbxdf.msgsDF(type='meeting', meetingId=meetingid)

    # get details and list of participants
    dfm=wbxdf.meetingDF(meetingid)
    emails = dfm.get_participants_emails()
    meetingDetails = dfm.details

    if ( meetingDetails and meetingDetails['state'] == 'ended'):

        # add messages sent by each participant from the time of the meeting start
        got_some_msgs=False
        for pe in emails:
            ut.trace(2, f"processing {pe}")
            dt_iso_ms=utils.datetime_to_iso_ms(meetingDetails['start'])
            filter={'from':dt_iso_ms}
            (c,d)=wbxr.get_user_msgs(pe, json.dumps(filter), "meetingMessages")
            if c:
                df=msgdf.add_msgs(pe, c, d)
                got_some_msgs=True
        
        # print (can be moved to meetingDF)
        if (got_some_msgs):
            print_in_meeting_user_msgs(df, csvfile, True)
        else:
            print("No messages found.")
    else:
        print(f"Meeting ID {meetingid} not found or not ended")
        


@click.group()
def meeting():
    pass

meeting.add_command(meeting_user_messages, name='user_messages') 
meeting.add_command(meeting_participants, name='participants')
meeting.add_command(meeting_messages, name='messages')
# meeting.add_command(fetch_meetings, name='fetch')
meeting.add_command(list_meetings_events, name='list')
meeting.add_command(meeting_details, name='details')


#####################
### Top Lev       ###
#####################

@click.group()
@click.version_option(__version__)
@click.option('-t', '--token', help='Your access token. Read from AUTH_BEARER env variable by default. You can find your personal token at https://developer.webex.com/docs/getting-started.')
@click.option('-d', '--debug', default=2, help='Debug level.')
def cli(debug, token):
    wbx_cpl.utils.DEBUG_LEVEL = debug
    if (debug >=3 ):
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
    if (token):
        # wbxr.set_token(token)
        wbx_cpl.wbx.ACCESS_TOKEN=token
    else:
        if ( 'AUTH_BEARER' in os.environ ):
            ut.trace(3, f"setting Access Token from env {os.environ['AUTH_BEARER']}")
            wbx_cpl.wbx.ACCESS_TOKEN=os.environ['AUTH_BEARER']
        else:
            sys.exit('No access token set. Use option -t or AUTH_BEARER env variable')

cli.add_command(messaging)
cli.add_command(meeting)
# cli.add_command(user)
cli.add_command(recording)

if __name__ == '__main__':
    cli()
