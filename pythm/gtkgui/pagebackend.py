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
import gobject
from page import Page
from pythm.lang import _
from pythm.backend import Signals
from gtkhelper import ImageButton
from pythm.config import PythmConfig
from pythm.backend.manager import BackendManager

class PageBackend(Page):
    def __init__(self):
        self.model = gtk.ListStore(object,str,str,str)
        Page.__init__(self)

        self.cfg = PythmConfig()

        self.btn_connect = ImageButton(gtk.STOCK_CONNECT)
        self.btnbox.add(self.btn_connect)
        self.btn_connect.connect("clicked",self.btn_connect_clicked)

        self.btn_start = ImageButton(gtk.STOCK_EXECUTE)
        self.btnbox.add(self.btn_start)
        self.btn_start.connect("clicked",self.btn_start_clicked)

        self.btn_stop = ImageButton(gtk.STOCK_STOP)
        self.btnbox.add(self.btn_stop)
        self.btn_stop.connect("clicked",self.btn_stop_clicked)

        self.btn_refresh = ImageButton(gtk.STOCK_REFRESH)
        self.btnbox.add(self.btn_refresh)
        self.btn_refresh.connect("clicked",self.btn_refresh_clicked)

        self.mgr = BackendManager()

        if self.cfg.get_backend() != None:
            self.start_backend(self.cfg.get_backend())


        self.refresh()
        self.row_selected(None)
        self.set_sensitive(True)

    def start_backend(self,backend):
        if self.mgr.start(backend,self.gtkcallback):
            self.mgr.connect(backend)



    def btn_start_clicked(self,btn):
        self.start_backend(self.get_selected())
        self.refresh()

    def btn_stop_clicked(self,btn):
        self.mgr.stop(self.get_selected())
        self.refresh()

    def btn_connect_clicked(self,btn):
        self.mgr.connect(self.get_selected())
        self.refresh()

    def btn_refresh_clicked(self,btn):
        self.refresh()


    def refresh(self):
        self.model.clear()
        for backend in self.mgr.get_backends():
            status = "inactive"
            if backend.is_started():
                status = "active"
            conn = "connected"
            if not backend.is_connected():
                conn ="disconnected"

            self.model.append([backend,backend.name,status,conn])


    def row_selected(self,path):
        backend = self.get_selected()
        if backend != None:
            self.btn_start.set_sensitive(not backend.is_started())
            self.btn_stop.set_sensitive(backend.is_started())
            self.btn_connect.set_sensitive(backend.is_started() and not backend.is_connected())
        else:
            self.btn_start.set_sensitive(False)
            self.btn_stop.set_sensitive(False)
            self.btn_connect.set_sensitive(False)

    def check_disabled(self,state):
        """overwritten"""
        pass

    def get_selected(self):
        iter = self.tv.get_selection().get_selected()[1]
        if iter is not None:
            return self.model.get_value(iter,0)
        return None

    def content(self):
        vbox = gtk.VBox()
        self.tv = gtk.TreeView(self.model)
        self.tv.get_selection().connect("changed", self.row_selected)

        colname = gtk.TreeViewColumn("Backend",gtk.CellRendererText(),text=1)
        colstatus = gtk.TreeViewColumn("State",gtk.CellRendererText(),text=2)
        colconnected = gtk.TreeViewColumn("Connected",gtk.CellRendererText(),text=3)

        self.tv.append_column(colname)
        self.tv.append_column(colstatus)
        self.tv.append_column(colconnected)

        sc = gtk.ScrolledWindow()
        sc.set_property("vscrollbar-policy",gtk.POLICY_AUTOMATIC)
        sc.set_property("hscrollbar-policy",gtk.POLICY_AUTOMATIC)
        sc.add(self.tv)
        vbox.pack_start(sc,False,False,0)

        return vbox

    def gtkcallback(self,func,*args):
        """
        callback method for signals of backend (out of gtk-thread)
        """
        gobject.idle_add(func,*args)
