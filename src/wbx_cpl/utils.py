import inspect
import re
import datetime

DEBUG_LEVEL=2

class UtilsTrc:
    def __init__ (self):
        pass

    def trace(self, lev, msg):
        caller = inspect.stack()[1][3]
        if ( DEBUG_LEVEL >= lev ):
            print(f"{caller}: {msg}")

def is_email_format(id):
    m = re.search(".+@.+[.].+$", id)
    if (m) :
        return (True)
    else:
        return(False)

# date time format required for Wbx 
def datetime_to_iso_ms(dtStr):
    dt=dt=datetime.datetime.fromisoformat(dtStr)
    iso_ms = dt.isoformat(timespec='milliseconds')
    return (re.sub('\+.+','', iso_ms) + 'Z')

