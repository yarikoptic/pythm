# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the pythm for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
""" TODO: Module description """

import pygtk
pygtk.require('2.0')
import gtk
from pythm.config import PythmConfig
from pythm.backend import State,Signals

class Page(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)
        self.cfg = PythmConfig()
        self.cfg.get_backend().connect(Signals.STATE_CHANGED,self.check_disabled)
        self.cfg.get_backend().connect(Signals.COMMAND_STATE,self.check_cmdstate)
        self.add(self.content())
        self.btnbox = gtk.HBox()
        self.pack_start(self.btnbox,False,False,0)
        self.set_sensitive(False)
        self.cmdimg = gtk.image_new_from_stock(gtk.STOCK_NETWORK, gtk.ICON_SIZE_LARGE_TOOLBAR)
        self.cmdimg.set_padding(3,3)
        self.cmdimg.set_sensitive(False)
        self.btnbox.pack_start(self.cmdimg,False,False,0)

    def check_cmdstate(self,state):
        self.cmdimg.set_sensitive(not state)

    def check_disabled(self,newstate):
        if newstate == State.DISABLED:
            self.set_sensitive(False)
        else:
            self.set_sensitive(True)




