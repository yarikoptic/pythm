import pygtk
pygtk.require('2.0')
import gtk
from page import Page
from pythm.lang import _
from pythm.backend import Signals
from gtkhelper import ImageButton,get_scrolled_widget

class PageBrowse(Page):
    def __init__(self):
        self.model = gtk.ListStore(object,str,gtk.gdk.Pixbuf)
        Page.__init__(self)

        self.btn_up = ImageButton(gtk.STOCK_GO_UP)
        self.btnbox.add(self.btn_up)
        self.btn_up.connect("clicked",self.btn_up_clicked)
                
        self.btn_add = ImageButton(gtk.STOCK_ADD)
        self.btnbox.add(self.btn_add)
        self.btn_add.connect("clicked",self.btn_add_clicked)
        
        self.btn_adddir= ImageButton(gtk.STOCK_DIRECTORY)
        self.btnbox.add(self.btn_adddir)
        self.btn_adddir.connect("clicked",self.btn_adddir_clicked)
        self.path = None
        
        self.cfg.get_backend().connect(Signals.BROWSER_CHANGED,self.browser_changed)

    def btn_adddir_clicked(self,btn):
        entry = self.get_selected_entry()
        if entry != None and entry.isDir:
            self.cfg.get_backend().add_dir(entry.id)
    
    def btn_up_clicked(self,btn):
        self.cfg.get_backend().browse_up(self.path)
    
    def btn_add_clicked(self,btn):
        self.add_selected_entry()
        
    def browser_changed(self,path,list):
        self.path = path
        self.model.clear()
        for f in list:
            if f.isDir:
                pbuf = self.get_icon_pixbuf('STOCK_DIRECTORY')
            else:
                pbuf = self.get_icon_pixbuf('STOCK_FILE')
                
            self.model.append([f,f.caption,pbuf])
            
    def get_icon_pixbuf(self, stock):
        return self.tv.render_icon(stock_id=getattr(gtk, stock),
                                size=gtk.ICON_SIZE_MENU,
                                detail=None)
    
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
                self.cfg.get_backend().browse(entry.id)
            else:
                self.cfg.get_backend().add(entry.id)
        
        
    def content(self):
        vbox = gtk.VBox()
        self.tv = gtk.TreeView(self.model)
        self.tv.connect("row_activated", self.row_activated)
        
        #tv.append_column(gtk.TreeViewColumn("No",gtk.CellRendererText(),text=0))
        rend = gtk.CellRendererPixbuf()
        col_dir = gtk.TreeViewColumn("Dir")
        col_dir.pack_start(rend,expand=False)
        col_dir.add_attribute(rend,'pixbuf',2)
        col_file = gtk.TreeViewColumn("File",gtk.CellRendererText(),text=1)
        self.tv.append_column(col_dir) 
        self.tv.append_column(col_file)     
        sc = get_scrolled_widget()
        #sc = gtk.ScrolledWindow()
        #sc.set_property("vscrollbar-policy",gtk.POLICY_AUTOMATIC)
        #sc.set_property("hscrollbar-policy",gtk.POLICY_AUTOMATIC)
        
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
        