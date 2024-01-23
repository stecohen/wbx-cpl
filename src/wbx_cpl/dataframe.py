import pandas as pd 
pd.set_option('display.max_colwidth', 80)
import wbx_cpl.utils 
from wbx_cpl.wbx import WbxRequest as Wbxr

ut=wbx_cpl.utils.UtilsTrc()
wbxr=Wbxr()

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

        ut.trace (3, f"{ue}, {cr_msgs}, {dl_msgs}, {add_title}, {IsSpace}")

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
                        fn=wbxr.extract_file_name(hds['content-disposition'])
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
                        other_member=self.get_other_person_membership(msg['roomId'],msg['personId'])
                        # title=f"{other_member['personDisplayName']} ({other_member['personEmail']})"
                        title=f"{other_member['personEmail']}"
                    else:
                        ut.trace (3, "space message, getting room title")
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

