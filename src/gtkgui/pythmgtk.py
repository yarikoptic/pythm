import pygtk
pygtk.require('2.0')
import gtk

from pagelist import *
from pageplay import *
from pagebrowse import *

class PythmGtk:

    def hello(self, widget, data=None):
        print "Hello World"

    def delete_event(self, widget, event, data=None):
        print "delete event occurred"
        # Change FALSE to TRUE and the main window will not be destroyed
        return False

    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        gtk.main_quit()
        self.backend.shutdown()

    def __init__(self,backend):
        # create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.resize(480,640)

        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        
        self.backend = backend
    
    
        #self.button = gtk.Button("Hello World")
        #self.button.connect("clicked", self.hello, None)
        #self.button.connect_object("clicked", gtk.Widget.destroy, self.window)
        self.vbox = gtk.VBox()
        self.tabs = gtk.Notebook()
        self.tabs.append_page(PagePlay(self.backend),gtk.Label("Play"))
        self.tabs.append_page(PageList(self.backend),gtk.Label("List"))
        self.tabs.append_page(PageBrowse(self.backend),gtk.Label("Browse"))

        self.vbox.add(self.tabs)
        
    
        # This packs the button into the window (a GTK container).
        self.window.add(self.vbox)
        
        # and the window
        self.window.show_all()
        
        self.backend.add("/home/ugh/music/ogg/amon amarth/versus the world/05 - amon amarth - across the rainbow bridge.ogg")
        
