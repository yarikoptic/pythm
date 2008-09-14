import pygtk
pygtk.require('2.0')
import gtk
import gobject

from pagelist import *
from pageplay import *
from pagebrowse import *
from pythm.lang import _


class PythmGtk:

    def hello(self, widget, data=None):
        print "Hello World"

    def delete_event(self, widget, event, data=None):
        print "delete event occurred"
        # Change FALSE to TRUE and the main window will not be destroyed
        return False

    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        self.backend.shutdown()
        gtk.main_quit()

    def __init__(self,backendClass):
        # create a new window
        gtk.gdk.threads_init()
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.resize(480,640)
        self.window.set_title(_("pythm"))

        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        
        self.backend = backendClass(self.gtkcallback)
        #self.button = gtk.Button("Hello World")
        #self.button.connect("clicked", self.hello, None)
        #self.button.connect_object("clicked", gtk.Widget.destroy, self.window)
        self.vbox = gtk.VBox()
        self.tabs = gtk.Notebook()
        self.tabs.set_property("homogeneous",True)
        play = PagePlay(self.backend)
        self.tabs.append_page(play,gtk.Label("Play"))
        self.tabs.child_set(play,"tab-expand",True)
        
        self.tabs.append_page(PageList(self.backend),gtk.Label("List"))
        self.tabs.append_page(PageBrowse(self.backend),gtk.Label("Browse"))

        self.vbox.add(self.tabs)
        
    
        # This packs the button into the window (a GTK container).
        self.window.add(self.vbox)
        
        # and the window
        self.window.show_all()
        
        #initialize
        self.backend.populate()
        
        gtk.main()


    def gtkcallback(self,func,*args):
        """
        callback method for signals of backend (out of gtk-thread)
        """
        gobject.idle_add(func,*args)
        
