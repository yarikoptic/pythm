# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the pythm for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Configuration 'Manager' for pythm"""

import os
import logging
import warnings
from ConfigParser import *

import backend

logger = logging.getLogger("pythm")

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
            logger.debug("Initializing configuration")
            self._ready = True
            ConfigParser.__init__(self)
            cfgfile =  os.path.join(os.path.expanduser("~"),
                                    ".pythm", "pythm.conf")
            if not os.path.exists(cfgfile):
                cfgfile = "/etc/pythm.conf"

            self.read(cfgfile)
            self.backends = []
            self.backend = backend.DummyBackend()
            self.callbacks = {}
            self.initialize_backends()
            self._wfilter = []
            """Already reported warnings. So we could report only once"""

    def initialize_backends(self):
        defaultbackend = self.get("pythm", "backend", None)
        logger.debug("Using %s backend" % defaultbackend)
        backends = self.get_commaseparated("pythm", "backends",
                                           "mpd,mplayer,gstreamer")
        for b in backends:
            try:
                module = self.my_import("pythm."+b)
                instance = backend.ThreadedBackend(module.backendClass())
                self.backends.append(instance)
                if b == defaultbackend:
                    self.backend = instance
            except Exception,e:
                logger.error("Could not load backend '%s' due to '%s'" % (b, e))

    def my_import(self, name):
        mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod


    def _warn(self, wstr):
        """Issue a warning to the logger, make sure that it is done only once
        """
        if not wstr in self._wfilter:
            self._wfilter.append(wstr)
            logger.warn(wstr)

    def get(self, section, option, default=None, dtype=None):
        """Returns the value for a configuration option

        :Parameters:
          section
            Name of the section in a configuration file
          option
            Name of the option
          default
            Value to be provided if configuration file does not
            contain a corresponding section/option
        """
        ret = default
        try:
            ret = ConfigParser.get(self, section, option)
        except Exception, e:
            self._warn("Assuming the %s.%s=%s since no option is found "
                       "in configuration file: %s" %
                       (section, option, default, str(e)))

        if dtype is not None:
            try:
                ret = dtype(ret)
            except Exception, e:                # could be ValueError, TypeError
                self._warn("Assuming default %s.%s=%s since failed to "
                           "convert '%s' using %s: %s" %
                           (section, option, default, ret, dtype, str(e)))
                ret = default
        return ret

    def get_commaseparated(self,section,option,default):
        """
        returns an array of comma separated options
        """
        data = self.get(section,option,default)
        return data.split(",")


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


