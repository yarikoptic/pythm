import pygtk
pygtk.require('2.0')
import gtk
import signal

from pagelist import *
from pageplay import *
from pagebrowse import *
from pagebackend import *
from pythm.lang import _
from pythm.backend import ThreadedBackend
from pythm.config import PythmConfig

class PythmGtk:

    def hello(self, widget, data=None):
        print "Hello World"

    def delete_event(self, widget, event, data=None):
        print "delete event occurred"
        # Change FALSE to TRUE and the main window will not be destroyed
        return False

    def win_redraw(self, widget, event):
	self.window.queue_draw()

    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        for backend in self.cfg.get_backends():
            backend.shutdown()
        gtk.main_quit()

    def __init__(self):
	# install signal handler to quit on Ctrl-C
	signal.signal(signal.SIGINT, self.destroy)

        # create a new window
        gtk.gdk.threads_init()
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
	self.window.connect("focus-in-event", self.win_redraw)

	#ptt : try to load size from config file, else go fullscreen
        self.cfg = PythmConfig()

        size = self.cfg.get_commaseparated("pythm","size","0,0")
	if (int(size[0]) > 0):
	    self.window.resize(int(size[0]),int(size[1]))
	else:
            self.window.maximize()

        self.window.set_title("Pythm")

        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        
        self.vbox = gtk.VBox()
        self.tabs = gtk.Notebook()
        self.tabs.set_property("homogeneous",True)
	#ptt
        self.tabs.set_property("tab_vborder",15)
        play = PagePlay()
        img = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
        img.set_padding(3,3)
        self.tabs.append_page(play,img)
        self.tabs.child_set(play,"tab-expand",True)
        img = gtk.image_new_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_BUTTON)
        img.set_padding(3,3)        
        self.tabs.append_page(PageList(),img)
        img = gtk.image_new_from_stock(gtk.STOCK_FIND, gtk.ICON_SIZE_BUTTON)
        img.set_padding(3,3)
        self.tabs.append_page(PageBrowse(),img)
        
        img = gtk.image_new_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON)
        img.set_padding(3,3)
        box = gtk.HBox()
        self.tabs.append_page(PageBackend(),img)

        self.vbox.add(self.tabs)
    
        # This packs the button into the window (a GTK container).
        self.window.add(self.vbox)
        
        # and the window
        self.window.show_all()

	#ptt : on opening switch directly to browse tab
        self.tabs.set_current_page(2)
            
        gtk.main()

