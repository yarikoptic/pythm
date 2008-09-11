import pygtk
pygtk.require('2.0')
import gtk

from page import Page

class PagePlay(Page):
    def __init__(self,backend):
        self.caption1 = "prev"
        self.caption2 = "play"
        self.caption3 = "next"
        Page.__init__(self,backend);
        
        
    def content(self):
        vbox = gtk.VBox()
        vbox.pack_start(gtk.Label("Track - Artist"),True,False,0)
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label("Vol."),False,False,0)
        vol_scale = gtk.HScale();
        vol_scale.set_property("draw-value",False)
        hbox.add(vol_scale)
        hbox2 = gtk.HBox()
        hbox2.pack_start(gtk.Label("Pos."),False,False,0)
        pos_scale = gtk.HScale();
        pos_scale.set_property("draw-value",False)
        hbox2.add(pos_scale)
        vbox.add(hbox2)
        vbox.add(hbox)
        return vbox