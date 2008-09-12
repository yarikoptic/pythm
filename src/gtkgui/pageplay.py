import pygtk
pygtk.require('2.0')
import gtk

from page import Page
from backend import Signals

class PagePlay(Page):
    def __init__(self,backend):
        self.caption1 = "prev"
        self.caption2 = "play"
        self.caption3 = "next"
        Page.__init__(self,backend);
        self.backend.connect(Signals.VOLUME_CHANGED,self.volume_changed)
        self.backend.connect(Signals.RANDOM_CHANGED,self.random_changed)
        self.backend.connect(Signals.REPEAT_CHANGED,self.repeat_changed)
        self.backend.connect(Signals.SONG_CHANGED,self.song_changed)
        self.backend.connect(Signals.POS_CHANGED,self.pos_changed)
        self.btn2.connect("clicked", self.btn2_clicked)

    def btn2_clicked(self,widget):        
        self.backend.play()

    def song_changed(self,newplentry):
        self.songlabel.set_label(str(newplentry))
        self.pos_scale.set_range(0,newplentry.length)
        self.pos_changed(0)

    def pos_changed(self,newPos):
        newPos = int(newPos)
        self.pos_scale.set_value(newPos)
        min = int(newPos / 60)
        sec = int(newPos % 60)
        if sec < 10:
            sec = "0" + str(sec)
        
        lbl = str(min) + ":" + str(sec)
        self.timelabel.set_label(lbl)
        
    def random_changed(self,newRand):
        self.random.set_active(newRand)
        
    def repeat_changed(self,newRept):
        self.repeat.set_active(newRept)

    def volume_changed(self,newVolume):
        self.vol_scale.set_value(newVolume)
    
    def content(self):
        #track info
        vbox = gtk.VBox()
        self.songlabel = gtk.Label("")
        vbox.pack_start(self.songlabel,True,True,0)
        self.timelabel = gtk.Label("00:00")
        vbox.pack_start(self.timelabel,True,True,0)
        
        #pos slider
        hbox2 = gtk.HBox()
        hbox2.pack_start(gtk.Label("Pos."),False,False,0)
        self.pos_scale = gtk.HScale();
        self.pos_scale.set_property("draw-value",False)
        hbox2.add(self.pos_scale)
        vbox.add(hbox2)
        
        #volume,random,repeat
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label("Vol."),False,False,0)
        self.vol_scale = gtk.HScale();
        self.vol_scale.set_range(0,100)
        self.vol_scale.set_property("draw-value",False)
        hbox.add(self.vol_scale)
        self.random = gtk.CheckButton(label="random")
        hbox.pack_start(self.random,False,False,0)
        self.repeat = gtk.CheckButton(label="repeat")
        hbox.pack_start(self.repeat,False,False,0)
        self.random.connect("toggled",self.on_random)
        self.repeat.connect("toggled",self.on_repeat)
        
        vbox.add(hbox)
        
        return vbox
    
    def on_random(self,widget):
        self.backend.set_random(widget.get_active())
        
    def on_repeat(self,widget):
        self.backend.set_repeat(widget.get_active())
        