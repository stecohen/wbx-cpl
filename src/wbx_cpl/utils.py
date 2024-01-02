import inspect
import re

class UtilsTrc:
    def __init__ (self):
        pass
    
    def setDebugLevel(self, deb):
        self.debug_lev = deb

    def trace(self, lev, msg):
        caller = inspect.stack()[1][3]
        if ( self.debug_lev >= lev ):
            print(f"{caller}: {msg}")


def is_email_format(id):
    m = re.search(".+@.+[.].+$", id)
    if (m) :
        return (True)
    else:
        return(False)

