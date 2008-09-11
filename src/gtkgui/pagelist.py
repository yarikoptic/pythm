import pygtk
pygtk.require('2.0')
import gtk
from backend import Signals

from page import Page

class PageList(Page):
    def __init__(self,backend):
        self.caption1 = "up"
        self.caption2 = "down"
        self.caption3 = "del"
        self.model = gtk.ListStore(int,str,str,int)
        Page.__init__(self,backend)
        self.backend.connect(Signals.PLAYLIST_CHANGED,self.loadList)
        self.loadList()
        
    def loadList(self):
        pl = self.backend.get_pl()
        self.model.clear()
        for p in pl:
            self.model.append([int(p.id),p.artist,p.title,int(p.length)])
                
        
    def content(self):
        vbox = gtk.VBox()
        tv = gtk.TreeView(self.model)
        #tv.append_column(gtk.TreeViewColumn("No",gtk.CellRendererText(),text=0))
        tv.append_column(gtk.TreeViewColumn("Artist",gtk.CellRendererText(),text=1))
        tv.append_column(gtk.TreeViewColumn("Title",gtk.CellRendererText(),text=2))       
        tv.append_column(gtk.TreeViewColumn("Length",gtk.CellRendererText(),text=3)) 
        sc = gtk.ScrolledWindow()
        sc.add(tv)
        vbox.pack_start(sc,True,True,0)
        return vbox