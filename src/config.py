#!/usr/bin/env python
import os
from ConfigParser import *

class PythmConfig(ConfigParser):
    """
    configuration object for pythm
    """
    
    __shared_state = {}
    
    def __init__(self):
        """
        Init with Borg-Pattern (= Singleton)
        """
        self.__dict__ = self.__shared_state
        if not '_ready' in dir(self):
            self._ready = True
            ConfigParser.__init__(self)
            cfgfile =  os.path.join(os.path.expanduser("~"), ".pythm")
            self.read(cfgfile)

        
    def get(self, section, option, default=None):
        """
        returns the configuration Option or the provided Default value, if the section or option does not exist.
        """
        ret = default
        try:
            ret = ConfigParser.get(self, section, option)
        except:
            pass
        return ret

