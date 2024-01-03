import wbx_cpl.utils as utils
import requests
import re

class WbxRequest:

    accessToken = ""
    spark_header = {}

    def __init__(self, ut) -> None:
        self.ut = ut

    def set_token(self, tok):
        self.accessToken=tok
        self.spark_header = {'Authorization': f"Bearer {tok}", 'Content-Type': 'application/json; charset=utf-8'}

    #sets the header to be used for authentication and data format to be sent.
    def setHeaders(self):
        spark_header = {'Authorization': f"Bearer {self.accessToken}", 'Content-Type': 'application/json; charset=utf-8'}

    # generic get data 
    # returns {} if not happy  
    #
    def get_wbx_data(self, ep, params="", ignore_error=False):
        url = "https://webexapis.com/v1/" + ep + params
        self.ut.trace(3, f"{url} ")
        try:
            r = requests.get(url, headers=self.spark_header)
            s = r.status_code
            if (s == 200):
                d = r.json()
                self.ut.trace(3, f"success")  
                return(d)
            else:
                not ignore_error and self.ut.trace(1,f"error {url} {s}: {r.reason}")  
                return({})
        except requests.exceptions.RequestException as e:
            self.ut.trace(1, f"error {e}")

    # returns user data json 
    # returns "" if not found or some error   
    #
    def get_user_details(self, email_or_uid): 
        self.ut.trace (3, f"processing user {email_or_uid}")  

        if ( utils.is_email_format(email_or_uid)):
            uid = self.get_user_id(email_or_uid)
            if (uid=="") :
                return ""
        else:
            uid=email_or_uid

        url=f"https://webexapis.com/v1/people/{uid}"
        r = requests.request("GET", url, headers=self.spark_header)
        s = r.status_code
        if s == 200 :
            self.ut.trace(3,f"found {uid}")
            return(r.json())
        else:
            self.ut.trace(1,f"did not find {uid}")
            return("")

    
    # returms user id of given user email address 
    # returns "" if not found or some error   
    #
    def get_user_id(self, ue, ignore_error=False):
        # disable warnings about using certificate verification
        requests.packages.urllib3.disable_warnings()
        # get_user_url=urllib.parse.quote("https://webexapis.com/v1/people?email=" + ue)
        get_user_url="https://webexapis.com/v1/people?email=" +ue

        self.ut.trace (3, f"calling {get_user_url}")  
        # send GET request and do not verify SSL certificate for simplicity of this example
        r = requests.get(get_user_url, headers=self.spark_header, verify=True)
        s = r.status_code
        if s == 200 :
            j = r.json()
            if ( len(j["items"]) == 0 ):
                not ignore_error and self.ut.trace (1, f"user email {ue} not found")
                return("")
            else:
                if ( len(j["items"]) > 1 ):
                    self.ut.trace(1, f"Error found more than one match for user {ue}")
                    return(-2)
                if ( len(j["items"]) == 1 ):
                    u = j["items"][0]
                    self.ut.trace (3,f"email {ue} found {u['id']} ")
                    return(u['id'])     
        elif s == 404:
            not ignore_error and self.ut.trace(1,f"got error {s}: {r.reason}")  
            return("")
        else :
            self.ut.trace(1,f"got error {s}: {r.reason}")  
            return("")
        
    # generic head request  
    # 
    def req_head(self, url):
        self.ut.trace(3, f"{url} ")
        try:
            r = requests.head(url, headers=self.spark_header)
            s = r.status_code
            if (s == 200):
                d = r.headers
                self.ut.trace(3, f"success")  
                return(d)
            else:
                self.ut.trace(1,f"error {s}: {r.reason}")
                return({})
        except requests.exceptions.RequestException as e:
            self.uttrace(1, f"error {e}")
            return({})

    # generic events API 
    # 
    def get_events(self, opts):
        url=f"https://webexapis.com/v1/events{opts}"
        self.ut.trace(3, f"{url} ")
        try:
            r = requests.get(url, headers=self.spark_header)
            s = r.status_code
            if (s == 200):
                d = r.json()
                self.ut.trace(3, f"success")  
                return(d)
            else:
                self.ut.trace(1,f"error {s}: {r.reason}")  
        except requests.exceptions.RequestException as e:
            self.ut.trace(1, f"error {e}")

    # get membership list for given room id  
    # 
    def get_space_memberships(self, rid, ignore_error=False):
        url=f"https://webexapis.com/v1/memberships/?roomId={rid}"
        self.ut.trace(3, f"{url} ")
        try:
            r = requests.get(url, headers=self.spark_header)
            s = r.status_code
            if (s == 200):
                d = r.json()
                self.ut.trace(3, f"success for get_memberships")  
                return(d)
            else:
                not ignore_error and self.ut.trace(1,f"get_memberships error {s}: {r.reason}")
                self.ut.trace(3, f"error {s}: {r.reason} ")  
                return({})
        except requests.exceptions.RequestException as e:
            self.ut.trace(1, f"error {e}")

    # download url contents   
    # 
    def download_contents(self, url):
        hds=self.req_head(url)
        if ('Content-Disposition' in hds ):
            cd=hds['Content-Disposition'] 
            self.ut.trace(3, f"got file {str(hds)}")
            file_name = re.findall('filename="(.+)"', cd)[0]
            if file_name:
                try:    
                    with requests.get(url, headers=self.spark_header) as r:
                        with open(file_name, mode="wb") as f:
                            f.write(r.content)
                            print(f"{file_name} downloaded.")
                except:
                    self.ut.trace(1, f"Error downloading {url}")
            else:
                self.ut.trace(1, f"cannot extract filename in {cd}")
        else:
            self.ut.trace(1, f"no content-disposition in {url}")

