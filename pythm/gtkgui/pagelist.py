import pygtk
pygtk.require('2.0')
import gtk
import pango
from pythm.backend import Signals
from pythm.functions import format_time

from page import Page
from gtkhelper import ImageButton,get_scrolled_widget


class PageList(Page):
    def __init__(self):
	#id, artist, title, album, ('>' when playing)
        self.model = gtk.ListStore(object,str,str,str,str)
        Page.__init__(self)
        self.cfg.get_backend().connect(Signals.PL_CHANGED,self.load_list)
        self.cfg.get_backend().connect(Signals.PL_UPDATE,self.song_changed)
        self.cfg.get_backend().connect(Signals.SONG_CHANGED,self.song_changed)
	self.connect("focus", self.unselect_all)
        
        self.btn_up = ImageButton(gtk.STOCK_GO_UP)
        self.btnbox.add(self.btn_up)
        self.btn_down = ImageButton(gtk.STOCK_GO_DOWN)
        self.btnbox.add(self.btn_down)
        self.btn_play = ImageButton(gtk.STOCK_MEDIA_PLAY)
        self.btnbox.add(self.btn_play)        
        self.btn_clear = ImageButton(gtk.STOCK_CLEAR)
        self.btnbox.add(self.btn_clear)        
        self.btn_up.connect("clicked",self.clicked_up)
        self.btn_down.connect("clicked",self.clicked_down)
        self.btn_play.connect("clicked",self.clicked_play)
        self.btn_clear.connect("clicked",self.clicked_clear)

    def clicked_clear(self,widget):
        plid = self.get_selected_plid()
        if plid != None:
            self.cfg.get_backend().remove(plid)
	else:
            self.cfg.get_backend().clear()
        
    def clicked_up(self,widget):
        plid = self.get_selected_plid()
        if plid != None:
            self.cfg.get_backend().up(plid)
    
    def clicked_down(self,widget):
        plid = self.get_selected_plid()
        if plid != None:
            self.cfg.get_backend().down(plid)
            
    def clicked_play(self,widget):
        plid = self.get_selected_plid()
        self.cfg.get_backend().play(plid)

    def get_selected_plid(self):
        iter = self.tv.get_selection().get_selected()[1]
        if iter is not None:
            return self.model.get_value(iter,0)
        return None
        
    def song_changed(self,song):
        self.model.foreach(self.ch_song,song)
        
    def ch_song(self,model,path,iter,song):
        if song is not None and model.get_value(iter,0)==song.id:
	    model.set_value(iter,4,">")
	else:
	    model.set_value(iter,4,"")
        
    def unselect_all(self,dir,arg):
        self.tv.get_selection().unselect_all()

    def load_list(self,pl):
        self.model.clear()
        for p in pl:
            self.model.append([p.id,p.artist,p.title,p.album,""])

#    def _row_activated_handler(self, treeview, path, col):
#	print "handler"
#	selected = treeview.get_selection().get_selected_rows()
#        if not selected or len(selected) > 1:
#	    return
#	_iter = model.get_iter(selected[0])
#        number = model.get_value(_iter, 2)
#	print number

    def content(self):
        vbox = gtk.VBox()
        self.tv = gtk.TreeView(self.model)
	#TODO enable multi select work on list w/out ctrl or shift
	#self.tv.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        #self.tv.connect('row-activated', self._row_activated_handler)


	listfont = self.cfg.get("pythm","listfont",None)
	col_rendr = gtk.CellRendererText()
	if listfont is not None:
	    col_rendr.set_property("font-desc", pango.FontDescription(listfont))

	#ptt play state
#	stat_rendr= gtk.CellRendererPixbuf()
#       col_state = gtk.TreeViewColumn("")
#	col_state.add_attribute(stat_rendr,'pixbuf',4)
        col_state = gtk.TreeViewColumn("",col_rendr,text=4)
        self.tv.append_column(col_state)

        col_title = gtk.TreeViewColumn("Title",col_rendr,text=2)
        col_title.set_resizable(True)
        self.tv.append_column(col_title)
        col_artist = gtk.TreeViewColumn("Artist",col_rendr,text=1)
        col_artist.set_resizable(True)
        self.tv.append_column(col_artist)

        sc = get_scrolled_widget()
        
        sc.add(self.tv)
        vbox.pack_start(sc,True,True,0)
        return vbox
    
