import pygtk
pygtk.require('2.0')
import gtk
from page import Page
from pythm.lang import _

class PageBrowse(Page):
    def __init__(self,backend):
        self.model = gtk.ListStore(object,str,bool)
        Page.__init__(self,backend)

        self.btn_up = gtk.Button("up")
        self.btnbox.add(self.btn_up)
        self.btn_up.connect("clicked",self.btn_up_clicked)
                
        self.btn_add = gtk.Button("add")
        self.btnbox.add(self.btn_add)
        self.btn_add.connect("clicked",self.btn_add_clicked)
        
        self.btn_adddir= gtk.Button("add dir")
        self.btnbox.add(self.btn_adddir)
        self.btn_adddir.connect("clicked",self.btn_adddir_clicked)
        self.path = None
        
        self.load_list()
    
    def btn_adddir_clicked(self,btn):
        entry = self.get_selected_entry()
        if entry.isDir:
            self.backend.add_dir(entry.id)
    
    def btn_up_clicked(self,btn):
        path = self.backend.browse_up(self.path)
        if path != None:
            self.path = path
            self.load_list(path)
        
    
    def btn_add_clicked(self,btn):
        self.add_selected_entry()
        
    def load_list(self,path=None):
        br = self.backend.browse(path)
        self.path = path
        self.model.clear()
        for f in br:
            self.model.append([f,f.caption,f.isDir])
            
    
    def row_activated(self, tv, path, view_column):
        self.add_selected_entry()
        
    def get_selected_entry(self):
        iter = self.tv.get_selection().get_selected()[1]
        if iter is not None:
            return self.model.get_value(iter,0)
        return None
    
    def add_selected_entry(self):
        entry = self.get_selected_entry()
        if entry != None:
            if entry.isDir:
                self.load_list(entry.id)
            else:
                self.backend.add(entry.id)
        
        
    def content(self):
        vbox = gtk.VBox()
        self.tv = gtk.TreeView(self.model)
        self.tv.connect("row_activated", self.row_activated)
        
        #tv.append_column(gtk.TreeViewColumn("No",gtk.CellRendererText(),text=0))
        rend = gtk.CellRendererText()
        colDir = gtk.TreeViewColumn("Dir",rend,text=2)
        colDir.set_cell_data_func(rend, dirRender)
        colFile = gtk.TreeViewColumn("File",gtk.CellRendererText(),text=1)
        self.tv.append_column(colDir) 
        self.tv.append_column(colFile)     
        sc = gtk.ScrolledWindow()
        sc.set_property("vscrollbar-policy",gtk.POLICY_AUTOMATIC)
        sc.set_property("hscrollbar-policy",gtk.POLICY_AUTOMATIC)
        sc.add(self.tv)
        vbox.pack_start(sc,True,True,0)
        return vbox
    
def dirRender(column, cell_renderer, model, iter):
    if model.get_value(iter, 2):
        val = "D"
    else:
        val = "F"
    cell_renderer.set_property('text', val)
    return
        