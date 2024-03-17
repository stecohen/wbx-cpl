import wbx_cpl.utils as utils
import datetime 
from datetime import timezone
import requests
import json
import re

ut=utils.UtilsTrc()

# move this to wbx.py
now = datetime.datetime.now(timezone.utc)
nowiso = now.isoformat(timespec='milliseconds')
UTCNOW = re.sub('\+.+','', nowiso) + 'Z' # remove the tz suffix 

ACCESS_TOKEN=""

class WbxRequest:

    def __init__(self) :
        pass

    def set_token(self, tok):
        ACCESS_TOKEN=tok
        ut.trace(3, f"Setting access token {ACCESS_TOKEN}")

    #sets the header to be used for authentication and data format to be sent.
    def setHeaders(self):
        ut.trace(3, f"access token is {ACCESS_TOKEN}")
        spark_header = {'Authorization': f"Bearer {ACCESS_TOKEN}", 'Content-Type': 'application/json; charset=utf-8'}
        return(spark_header)

    # extracts file name from content disposition header field 
    def extract_file_name(self, cd):
        name=re.findall('filename="(.+)"', cd)[0]
        return(name)

    # generic get data 
    # returns {} if not happy  
    #
    def get_wbx_data(self, ep, params="", ignore_error=False):
        url = "https://webexapis.com/v1/" + ep + params
        ut.trace(3, f"{url} ")
        hdr=self.setHeaders()
        try:
            r = requests.get(url, headers=hdr)
            s = r.status_code
            if (s == 200):
                d = r.json()
                ut.trace(3, f"success" )  
                return(d)
            else:
                not ignore_error and ut.trace(1,f"error {url} {s}: {r.reason}")  
                return({})
        except requests.exceptions.RequestException as e:
            ut.trace(1, f"error {e}")


    # returns user data json 
    # returns "" if not found or some error   
    #
    def get_user_details(self, email_or_uid): 
        ut.trace (3, f"processing user {email_or_uid}")  

        if ( utils.is_email_format(email_or_uid)):
            uid = self.get_user_id(email_or_uid)
            if (uid=="") :
                return ""
        else:
            uid=email_or_uid

        url=f"https://webexapis.com/v1/people/{uid}"
        r = requests.request("GET", url, headers=self.setHeaders())
        s = r.status_code
        if s == 200 :
            ut.trace(3,f"found {uid}")
            return(r.json())
        else:
            ut.trace(1,f"did not find {uid}")
            return("")

    
    # returms user id of given user email address 
    # returns "" if not found or some error   
    #
    def get_user_id(self, ue, ignore_error=False):
        # disable warnings about using certificate verification
        requests.packages.urllib3.disable_warnings()
        # get_user_url=urllib.parse.quote("https://webexapis.com/v1/people?email=" + ue)
        get_user_url="https://webexapis.com/v1/people?email=" +ue

        ut.trace (3, f"calling {get_user_url} T = {ACCESS_TOKEN}")  
        # send GET request and do not verify SSL certificate for simplicity of this example
        r = requests.get(get_user_url, headers=self.setHeaders(), verify=True)
        s = r.status_code
        if s == 200 :
            j = r.json()
            if ( len(j["items"]) == 0 ):
                not ignore_error and ut.trace (1, f"user email {ue} not found")
                return("")
            else:
                if ( len(j["items"]) > 1 ):
                    ut.trace(1, f"Error found more than one match for user {ue}")
                    return(-2)
                if ( len(j["items"]) == 1 ):
                    u = j["items"][0]
                    ut.trace (3,f"email {ue} found {u['id']} ")
                    return(u['id'])     
        elif s == 404:
            not ignore_error and ut.trace(1,f"got error {s}: {r.reason}")  
            return("")
        else :
            ut.trace(1,f"got error {s}: {r.reason}")  
            return("")
        
    # generic head request  
    # 
    def req_head(self, url):
        ut.trace(3, f"{url} ")
        try:
            r = requests.head(url, headers=self.setHeaders())
            s = r.status_code
            if (s == 200):
                d = r.headers
                ut.trace(3, f"success")  
                return(d)
            else:
                ut.trace(1,f"error {s}: {r.reason}")
                return({})
        except requests.exceptions.RequestException as e:
            ut.trace(1, f"error {e}")
            return({})

    # generic events API 
    # 
    def get_events(self, opts):
        url=f"https://webexapis.com/v1/events{opts}"
        ut.trace(3, f"{url} ")
        try:
            r = requests.get(url, headers=self.setHeaders())
            s = r.status_code
            if (s == 200):
                d = r.json()
                ut.trace(3, f"success")  
                return(d)
            else:
                ut.trace(1,f"error {s}: {r.reason}")  
                return({})
        except requests.exceptions.RequestException as e:
            ut.trace(1, f"error {e}")
            return({})


    # get membership list for given room id  
    # 
    def get_space_memberships(self, rid, ignore_error=False):
        url=f"https://webexapis.com/v1/memberships/?roomId={rid}"
        ut.trace(3, f"{url} ")
        try:
            r = requests.get(url, headers=self.setHeaders())
            s = r.status_code
            if (s == 200):
                d = r.json()
                ut.trace(3, f"success for get_memberships")  
                return(d)
            else:
                not ignore_error and ut.trace(1,f"get_memberships error {s}: {r.reason}")
                ut.trace(3, f"error {s}: {r.reason} ")  
                return({})
        except requests.exceptions.RequestException as e:
            ut.trace(1, f"error {e}")
            return({})


    # download url contents   
    # will use name from content dispostion by default
    # 
    def download_contents(self, url, dir="", name=""):
        hds=self.req_head(url)
        if ('Content-Disposition' in hds ):
            cd=hds['Content-Disposition'] 
            ut.trace(3, f"got file {str(hds)}")
            cd_name = re.findall('filename="(.+)"', cd)[0]
            if cd_name:
                if name:
                    file_name=name
                else:
                    file_name=cd_name                    
                try:    
                    with requests.get(url, headers=self.setHeaders()) as r:
                        with open(dir+file_name, mode="wb") as f:
                            f.write(r.content)
                            print(f"{dir}{file_name} downloaded.")
                except:
                    ut.trace(1, f"Error downloading {url}")
            else:
                ut.trace(1, f"cannot extract filename in {cd}")
        else:
            ut.trace(1, f"no content-disposition in {url}")

    
    # get the 'other' (apart from given 'uid') person membership in a direct 1:1 space
    # returns {} if not found
    #
    def get_other_person_membership(self, roomId, uid):
        ut.trace(3, f"{roomId} {uid} ")
        members=self.get_space_memberships(roomId, True)
        ut.trace(3, f"got {members}")
        if 'items' in members:
            for item in members['items']:
                if (item['id'] != uid):
                    return(item)
        return({})

    # returns created and deleted messages objs for given user email 
    # optional parameters passed as json string like '{"max":1000}'
    # returns empty obj if not found meetingMessages
    # 
    def get_user_msgs(self, ue, user_opts="", resource="messages"):

        ut.trace (3, f"params = {ue}, {user_opts}")

        uid = self.get_user_id(ue, True)
        frm = datetime.datetime.now(timezone.utc) - datetime.timedelta(30)
        frmiso = frm.isoformat(timespec='milliseconds')
        utcFrm = re.sub('\+.+','', frmiso) + 'Z' # remove the tz suffix 

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
            params=f"?resource={resource}&actorId={uid}&"
            for k in opts:
                params=f"{params}&{k}={opts[k]}"
            ut.trace (3, f"searching created msgs params = {params}")
            created=self.get_events(params)

            # now search for deleted messages so we can mark them as such
            #
            params=f"?resource={resource}&actorId={uid}&type=deleted"
            for k in opts:
                params=f"{params}&{k}={opts[k]}"
            ut.trace (3, f"searching deleted msgs params = {params}")
            deleted=self.get_events(params)

            return(created, deleted)

        else:
            ut.trace(1, f"cannot find user {ue}")
            return({},{})

    # returns created and deleted meeting messages objs for given user email 
    # optional parameters passed as json string like '{"max":1000}'
    # returns empty obj if not found
    # 
    def get_meeting_msgs(self, ue, user_opts=""):

        ut.trace (3, f"params = {ue}, {user_opts}")

        uid = self.get_user_id(ue, True)
        frm = datetime.datetime.now(timezone.utc) - datetime.timedelta(30)
        frmiso = frm.isoformat(timespec='milliseconds')
        utcFrm = re.sub('\+.+','', frmiso) + 'Z' # remove the tz suffix 

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
            params=f"?resource=meetingMessages&actorId={uid}&"
            for k in opts:
                params=f"{params}&{k}={opts[k]}"
            ut.trace (3, f"searching created msgs params = {params}")
            created=self.get_events(params)

            # now search for deleted messages so we can mark them as such
            #
            params=f"?resource=meetingMessages&actorId={uid}&type=deleted"
            for k in opts:
                params=f"{params}&{k}={opts[k]}"
            ut.trace (3, f"searching deleted msgs params = {params}")
            deleted=self.get_events(params)

            return(created, deleted)

        else:
            ut.trace(1, f"cannot find user {ue}")
            return({})

    # returns meetings evts list for user email or all sites by default
    # optional parameters passed as json string like '{"max":1000}'
    # returns empty obj if not found
    # 
    def get_meeting_events(self, ue="", user_opts=""):

        ut.trace (3, f"params = {user_opts}")

        actorIdParam=""
        if (ue):
            try:
                uid = self.get_user_id(ue, True)
                actorIdParam=f"&actorId={uid}"
            except:
                ut.trace(1, f"error host email {ue} not found.")
                return({})
        

        frm = datetime.datetime.now(timezone.utc) - datetime.timedelta(30)
        frmiso = frm.isoformat(timespec='milliseconds')
        utcFrm = re.sub('\+.+','', frmiso) + 'Z' # remove the tz suffix 

        to = UTCNOW
        opts = {'max': 100,'from':utcFrm,'to':to}

        # override default options w/ user options
        #
        if (user_opts):
            try:
                userOpts=json.loads(user_opts)
                if ( userOpts.get('from') or userOpts.get('to') ) : # erase time defaults 
                    opts = {'max': 100} # a bit dirty 
                for k in userOpts:
                    opts[k]=userOpts[k]
            except:
                ut.trace(1, f"error parsing {user_opts} not a valid JSON format")

        # construct url parameter string
        #
        params=f"?resource=meetings&type=ended{actorIdParam}"
        for k in opts:
            params=f"{params}&{k}={opts[k]}"
        ut.trace (3, f"searching meetings events msgs params = {params}")
        meetings=self.get_events(params)

        return(meetings)
