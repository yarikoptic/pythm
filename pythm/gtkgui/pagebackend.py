import pygtk
pygtk.require('2.0')
import gtk
import gobject
import os
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
        
	#ptt
        self.cfg.get_backend().connect(Signals.RANDOM_CHANGED,self.random_changed)
        self.cfg.get_backend().connect(Signals.REPEAT_CHANGED,self.repeat_changed)
        
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
        
	#ptt
        #random, repeat
        hbox3 = gtk.HBox()
        self.random = gtk.CheckButton(label="random")
        hbox3.pack_start(self.random,True,False,0)
        self.repeat = gtk.CheckButton(label="repeat")
        hbox3.pack_start(self.repeat,True,False,0)
        self.random.connect("toggled",self.on_random)
        self.repeat.connect("toggled",self.on_repeat)
        vbox.add(hbox3)

        #enable headphones
        hbox4 = gtk.HBox()
        self.headphones = gtk.CheckButton(label="headphones on")
        self.headphones.connect("toggled",self.headphones_switch)
        hbox4.pack_start(self.headphones,True,False,0)
        vbox.add(hbox4)

	# ptt version label
	self.versionlabel = gtk.Label()
	self.versionlabel.set_alignment(1,1)
	self.versionlabel.set_markup("<span size=\"x-small\">"+"0.5.1-ptt5"+"  </span>")
        vbox.pack_start(self.versionlabel,False,False,0)
        
        return vbox
    
    def gtkcallback(self,func,*args):
        """
        callback method for signals of backend (out of gtk-thread)
        """
        gobject.idle_add(func,*args)
    
    def on_random(self,widget):
        self.cfg.get_backend().set_random(widget.get_active())
        
    def on_repeat(self,widget):
        self.cfg.get_backend().set_repeat(widget.get_active())

    def random_changed(self,newRand):
        self.random.set_active(newRand)
        
    def repeat_changed(self,newRept):
        self.repeat.set_active(newRept)

    def headphones_switch(self,widget):
	if widget.get_active():
            switch_on  = self.cfg.get("cmd","headphones_on",None)
	    if switch_on is not None:
	        os.system(switch_on)
	else:
            switch_off = self.cfg.get("cmd","headphones_off",None)
	    if switch_off is not None:
	        os.system(switch_off)
        
