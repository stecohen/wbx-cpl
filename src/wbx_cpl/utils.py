import inspect
import re

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

