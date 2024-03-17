import pandas as pd 
pd.set_option('display.max_colwidth', 80)
import wbx_cpl.utils 
from wbx_cpl.wbx import WbxRequest as Wbxr
import json as json

from webexteamssdk import WebexTeamsAPI

ut=wbx_cpl.utils.UtilsTrc()
wbxr=Wbxr()

# populates df with data obj based cols list of fields
#
def update_df_data(df,  data, cols):    
    if 'items' in data:
        for item in data['items']:
            ut.trace(3, f"Processing item {item}")
            new_row={}
            for f in cols:
                itemdata = item['data']
                if f in itemdata :
                    new_row[f]=itemdata[f]
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        ut.trace(3, f"no items in {data}")
    return(df)

class msgsDF:

    cols_user = {'id':[], 'created':[], 'text':[], 'fileCount':[],'files':[], 'fileNames':[], 'roomType':[], 'roomId':[]}
    cols_space = {'id':[],'sentBy':[],'created':[], 'text':[], 'fileCount':[],'files':[], 'fileNames':[]}
    cols_user_in_meeting = {'id':[], 'sentBy':[], 'created':[], 'text':[], 'meetingId':[] }

    def __init__(self, type, **options ):

        self.type=type
        match type:
            case 'user':
                self.mycols=self.cols_user
            case 'space':
                self.mycols=self.cols_space
            case 'meeting':
                self.mycols=self.cols_user_in_meeting
            case _:
                exit(f"Internal Error: invalid type {type}")

        self.add_title=options.get('title') # boolean 
        self.meetingId=options.get('meetingId') # if meetingId is set then we're looking for messages posted in this meeting
        self.df = pd.DataFrame(self.mycols)
 
    def add_msgs(self, ue, cr_msgs, dl_msgs ):

        ut.trace (3, f"{ue}, {cr_msgs}, {dl_msgs}, {self.add_title} ")

        # error protection 
        # 
        if 'items' not in cr_msgs:
            ut.trace (2, f"no messages in " + str(msg))
            return
        
        # iterate deleted messages and store in dl_msgs_d
        # 
        dl_msgs_d={}
        if 'items' in dl_msgs:
            for item in dl_msgs['items']:
                msg=item['data']
                dl_msgs_d[msg['id']]=msg

        # iterate created messages
        # 
        for item in cr_msgs['items']:
            msg=item['data']
            title="N/A"
            ut.trace (3, f"got message: {msg['text']} {msg['created']} ")

            if (not self.meetingId or (msg['meetingId'] == self.meetingId)): # if InMeeting: only retain messages for this meeting
                # new row from msg
                # 
                new_row={}
                for i in self.mycols:
                    if i in msg:
                        new_row[i]=msg[i]

                # add deleted date info + sender
                #
                new_row['deleted']='N'
                if dl_msgs_d.get(new_row['id']):
                    new_row['deleted']='Y'     
                new_row['sentBy']=ue

                # process 'files' column : add 'fileCount' and 'fileNames' values
                # 
                if ( self.type != 'meeting'):
                    file_count=0
                    file_list=[]
                    if ('files' in msg):
                        ut.trace(3, f"Files in msg {msg}")
                        file_count = len(msg['files'])
                        fileURLs=msg['files']
                        for furl in fileURLs:
                            ut.trace(3, f"processing {furl}")
                            # read headers
                            hds=wbxr.req_head(furl)
                            if 'content-disposition' in hds:
                                fn=wbxr.extract_file_name(hds['content-disposition'])
                                file_list.append(fn)
                            else:
                                ut.trace(3, f"could not find 'content-disposition' header in {furl}")
                        new_row['fileNames']=file_list
                        ut.trace(3, f"got {new_row['fileNames']}")
                    new_row['fileCount'] = int(file_count)
                
                # add column 'title' if long process option... will need to extend to in_meeting messages
                # 
                if ( self.add_title ):
                    if 'roomId' in msg:
                        # direct rooms don't have a title. Need to extract the 'other' member in the space
                        if (msg['roomType'] == 'direct'):
                            ut.trace (3, "direct message, getting other person email " + str(locals()))
                            other_member=wbxr.get_other_person_membership(msg['roomId'],msg['personId'])
                            # title=f"{other_member['personDisplayName']} ({other_member['personEmail']})"
                            title=f"{other_member['personEmail']}"
                        else:
                            ut.trace (3, "space message, getting room title")
                            room=wbxr.get_wbx_data(f"rooms/{msg['roomId']}","")
                            if ('title' in room) :
                                title=room['title']
                        new_row['title']=title
                
                # finally add to DF  
                # 
                ut.trace (3, f"adding message: {msg['text']} {msg['created']} ")
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
  
class membershipDF:

    cols = {'personEmail':[],'personDisplayName':[],'created':[]}

    def __init__(self):
        mycols=self.cols
        self.df = pd.DataFrame(mycols)
        
    def add_data(self, members):
        #
        if 'items' in members:
            for mbr in members['items']:
                new_row={}
                for f in self.cols:
                    if f in mbr:
                        new_row[f]=mbr[f]
                self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            ut.trace(3, f"no membership data")
        # return DF
        return(self.df)

class meetingDF:

    cols = {'email':[],'displayName':[],'host':[]}

    def __init__(self, meetingId):
        mycols=self.cols
        self.df = pd.DataFrame(mycols)
        self.meetingId=meetingId
        self.df['host'] = self.df['host'].astype(bool)
        self.add_participants()
        self.add_details()

    def add_participants(self):
        #
        # get row data
        self.participants = wbxr.get_wbx_data(f"meetingParticipants", f"?meetingId={self.meetingId}")
        #
        # build DF
        if 'items' in self.participants:
            for part in self.participants['items']:
                ut.trace(3, f"Processing item {part}")
                new_row={}
                for f in self.cols:
                    if f in part:
                        new_row[f]=part[f]
                self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            ut.trace(3, f"Error listing participants in meeting ID {self.meetingId}")
    
    def print_participants(self, csvFile):
        print(self.df)
        csvFile and self.df.to_csv(csvFile, index=False)

    def get_participants_emails(self):
        emails=[]
        if (self.participants.get('items')):
            for part in self.participants['items']:
                emails.append(part['email'])
        return(emails)
    
    def add_details(self) :
        self.details=wbxr.get_wbx_data(f"meetings/{self.meetingId}")
 

class meetingsDF:

    datafile="meeting_list.json"
    cols = {'meetingId':[], 'title':[], 'created':[],}

    def __init__(self):
        mycols=self.cols
        self.df = pd.DataFrame(mycols)

    ''' All this WIP 

    def fetch_meetings(self, userOpts=""):
        # get raw data
        self.meeting_list = wbxr.get_meeting_events(userOpts)
        with open(self.datafile, 'w') as f:
            f.write(json.dumps(self.meeting_list))

    def list_meetings(self, userOpts=""):
        with open(self.datafile, 'r') as f:
            # meeting_list=json.loads(f.read())
            meeting_list = wbxr.get_meeting_events(userOpts)
            self.df=update_df_data(self.df, meeting_list, self.cols)
            print(self.df)        
    ''' 

    # print to screen and file if option on 
    #
    def print(self, csvdest):
        df = self.df.sort_values(by=['created'])
        print(df.loc[:, ~df.columns.isin([''])])
        if csvdest:
            df.to_csv(csvdest, index=False)
            ut.trace(2, f"{csvdest} written.")

    # pull from events, store and displays 
    #
    def list_meetings(self, email, csvdest, userOpts=""):
        meeting_list = wbxr.get_meeting_events(email, userOpts)
        if (meeting_list) :
            self.df=update_df_data(self.df, meeting_list, self.cols)
            self.print(csvdest)
        else :  
            print("Error")

# User DB WIP
class usersDF:

    datafile="user_list.json"
    cols = {'id':[],'emails':[],'displayName':[], 'status':[]}

    def __init__(self):
        mycols=self.cols
        self.df = pd.DataFrame(mycols)

    def fetch_data(self):
        # get raw data
        self.user_list = wbxr.get_wbx_data("people")
        with open(self.datafile, 'w') as f:
            f.write(json.dumps(self.user_list))

    def list_users(self):
        try: 
            f = open(self.datafile, 'r')
            self.user_list=json.loads(f.read())
            if 'items' in self.user_list:
                for item in self.user_list['items']:
                    ut.trace(3, f"Processing item {item}")
                    new_row={}
                    for f in self.cols:
                        if f in item:
                            new_row[f]=item[f]
                    self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
                else:
                    ut.trace(3, f"no data")
        except Exception as e: 
            print(e)
            exit(-1)
        print(self.df)        
        