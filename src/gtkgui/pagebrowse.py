import pygtk
pygtk.require('2.0')
import gtk

from page import Page

class PageBrowse(Page):
    def __init__(self,backend):
        self.caption1 = "add"
        self.caption2 = "up"
        self.caption3 = ""
        self.model = gtk.ListStore(str,str,bool)
        Page.__init__(self,backend)
        self.loadList()
        
    def loadList(self,path=None):
        br = self.backend.browse(path)
        self.model.clear()
        for f in br:
            self.model.append([f.id,f.caption,f.isDir])
            
    
    def row_activated(self, tv, path, view_column):
        iter = self.model.get_iter(path)
        if iter is not None:
            val = self.model.get_value(iter,0)
            isDir = self.model.get_value(iter,2)
            if isDir:
                self.loadList(val)
            else:
                self.backend.add(val)
                
            print val
        
        
    def content(self):
        vbox = gtk.VBox()
        self.tv = gtk.TreeView(self.model)
        self.tv.connect("row_activated", self.row_activated)
        
        #tv.append_column(gtk.TreeViewColumn("No",gtk.CellRendererText(),text=0))
        self.tv.append_column(gtk.TreeViewColumn("File",gtk.CellRendererText(),text=1))     
        self.tv.append_column(gtk.TreeViewColumn("Dir",gtk.CellRendererText(),text=2)) 
        sc = gtk.ScrolledWindow()
        sc.add(self.tv)
        vbox.pack_start(sc,True,True,0)
        return vbox