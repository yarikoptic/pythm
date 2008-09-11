import pygtk
pygtk.require('2.0')
import gtk

class Page(gtk.VBox):
    def __init__(self,backend):
        self.backend = backend;
        gtk.VBox.__init__(self)
        self.add(self.content())
        self.btnbox = gtk.HBox()
        self.btn1 = gtk.Button(self.caption1)
        self.btn2 = gtk.Button(self.caption2)
        self.btn3 = gtk.Button(self.caption3)
        self.btnbox.add(self.btn1)
        self.btnbox.add(self.btn2)
        self.btnbox.add(self.btn3)
        self.pack_start(self.btnbox,False,False,0)


        
        
        