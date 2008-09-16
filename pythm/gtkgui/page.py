import pygtk
pygtk.require('2.0')
import gtk
from pythm.config import PythmConfig

class Page(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)
        self.cfg = PythmConfig()
        self.add(self.content())
        self.btnbox = gtk.HBox()
        self.pack_start(self.btnbox,False,False,0)
        


        
        
        