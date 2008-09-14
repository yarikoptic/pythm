import pygtk
pygtk.require('2.0')
import gtk
from pythm.backend import Signals
from pythm.functions import format_time

from page import Page

class PageList(Page):
    def __init__(self,backend):
        self.model = gtk.ListStore(object,str,str,int)
        Page.__init__(self,backend)
        self.backend.connect(Signals.PL_CHANGED,self.load_list)
        self.backend.connect(Signals.SONG_CHANGED,self.song_changed)
        
        self.btn_up = gtk.Button("up")
        self.btnbox.add(self.btn_up)
        self.btn_down = gtk.Button("down")
        self.btnbox.add(self.btn_down)
        self.btn_play = gtk.Button("play")
        self.btnbox.add(self.btn_play)        
        self.btn_del = gtk.Button("del")
        self.btnbox.add(self.btn_del)        
        self.btn_up.connect("clicked",self.clicked_up)
        self.btn_down.connect("clicked",self.clicked_down)
        self.btn_play.connect("clicked",self.clicked_play)        
        self.btn_del.connect("clicked",self.clicked_del)
        
    def clicked_up(self,widget):
        plid = self.get_selected_plid()
        if plid != None:
            self.backend.up(plid)
    
    def clicked_down(self,widget):
        plid = self.get_selected_plid()
        if plid != None:
            self.backend.down(plid)
            
    def clicked_play(self,widget):
        plid = self.get_selected_plid()
        if plid != None:
            self.backend.play(plid)
            
    def clicked_del(self,widget):
        plid = self.get_selected_plid()
        if plid != None:
            self.backend.remove(plid)
    
    def get_selected_plid(self):
        iter = self.tv.get_selection().get_selected()[1]
        if iter is not None:
            return self.model.get_value(iter,0)
        return None
        
    def song_changed(self,song):
        self.model.foreach(self.ch_song,song)
        
    def ch_song(self,model,path,iter,song):
        if model.get_value(iter,0)==song.id:
            model.set_value(iter,1,song.artist)
            model.set_value(iter,2,song.title)
            model.set_value(iter,3,song.length)
        
    def load_list(self,pl):
        self.model.clear()
        for p in pl:
            self.model.append([p.id,p.artist,p.title,int(p.length)])
                
        
    def content(self):
        vbox = gtk.VBox()
        self.tv = gtk.TreeView(self.model)
        #tv.append_column(gtk.TreeViewColumn("No",gtk.CellRendererText(),text=0))
        self.tv.append_column(gtk.TreeViewColumn("Artist",gtk.CellRendererText(),text=1))
        self.tv.append_column(gtk.TreeViewColumn("Title",gtk.CellRendererText(),text=2))       
        rend = gtk.CellRendererText()
        colLength = gtk.TreeViewColumn("Length",rend,text=3)
        self.tv.append_column(colLength) 
        colLength.set_cell_data_func(rend, length_render)
        sc = gtk.ScrolledWindow()
        sc.set_property("vscrollbar-policy",gtk.POLICY_AUTOMATIC)
        sc.set_property("hscrollbar-policy",gtk.POLICY_AUTOMATIC)
        sc.add(self.tv)
        vbox.pack_start(sc,True,True,0)
        return vbox
    
def length_render(column, cell_renderer, model, iter):
    val = format_time(model.get_value(iter, 3))
    cell_renderer.set_property('text', val)
    return