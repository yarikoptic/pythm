import pygtk
pygtk.require('2.0')
import gtk

class Page(gtk.VBox):
    def __init__(self,backend):
        gtk.VBox.__init__(self)
        self.backend = backend;
        self.add(self.content())
        self.btnbox = gtk.HBox()
        self.pack_start(self.btnbox,False,False,0)
        


        
        
        