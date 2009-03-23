#!/usr/bin/env python
import os
from ConfigParser import *
import backend
import string

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
            #print "new conf"
            self._ready = True
            ConfigParser.__init__(self)
            cfgfile =  os.path.join(os.path.expanduser("~"), ".pythm", "pythm.conf")
            if not os.path.exists(cfgfile):
                cfgfile = "/etc/pythm.conf"
                
            self.read(cfgfile)
            self.backends = []
            self.backend = backend.DummyBackend()
            self.callbacks = {}
            self.initialize_backends()
            
    def initialize_backends(self):
        defaultbackend = self.get("pythm","backend",None)
        print "using " + str(defaultbackend) + " backend"
        backends = self.get_commaseparated("pythm","backends","mpd,mplayer")
        for b in backends:
            try:
                module = self.my_import("pythm."+b)
                instance = backend.ThreadedBackend(module.backendClass())
                self.backends.append(instance)
                if b == defaultbackend:
                    self.backend = instance
            except Exception, e :
                print "could not load backend " + b + ": " + str(e)
        
    def my_import(self,name):
        mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod
        
        
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
    
    def get_commaseparated(self,section,option,default):
        """
        returns an array of comma separated options
        """
        data = self.get(section,option,default)
        return data.split(",")

    def get_boolean(self,section,option,default):
        """
        returns a boolean
        """
        data = self.get(section,option,default)
	if string.upper(data) == "TRUE":
	    return True
	else:
	    return False

    def get_array(self,section,option):
        """
        returns an array option starting at 0
        example: filters0, filters1...
        """
        ret = []
        i = 0
        while 1:
            tmp = self.get(section,option+str(i),None)
            if tmp == None:
                break;
            ret.append(tmp)
            i += 1
        return ret;
    
    def set_active_backend(self, backend):
        #print "setactive", self.backend.name, backend.name
        self.backend = backend
        
    def get_backend(self):
        #print self.backend.name
        return self.backend
        
    def get_backends(self):
        return self.backends
    

