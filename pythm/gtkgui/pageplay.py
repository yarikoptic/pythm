import pygtk
pygtk.require('2.0')
import gtk

from page import Page
from pythm.backend import Signals,State
from pythm.functions import format_time
from gtkhelper import ImageButton

class PagePlay(Page):
    def __init__(self):
        Page.__init__(self);
        self.cfg.get_backend().connect(Signals.VOLUME_CHANGED,self.volume_changed)
        self.cfg.get_backend().connect(Signals.RANDOM_CHANGED,self.random_changed)
        self.cfg.get_backend().connect(Signals.REPEAT_CHANGED,self.repeat_changed)
        self.cfg.get_backend().connect(Signals.SONG_CHANGED,self.song_changed)
        self.cfg.get_backend().connect(Signals.POS_CHANGED,self.pos_changed)
        self.cfg.get_backend().connect(Signals.STATE_CHANGED,self.state_changed)
        
        self.btn_prev = ImageButton(gtk.STOCK_MEDIA_PREVIOUS)
        self.btnbox.add(self.btn_prev)
        self.btn_stop = ImageButton(gtk.STOCK_MEDIA_STOP)
        self.btnbox.add(self.btn_stop)
        self.btn_pause = ImageButton(gtk.STOCK_MEDIA_PAUSE)
        self.btnbox.add(self.btn_pause)
        self.btn_play = ImageButton(gtk.STOCK_MEDIA_PLAY)
        self.btnbox.add(self.btn_play)
        self.btn_next = ImageButton(gtk.STOCK_MEDIA_NEXT)
        self.btnbox.add(self.btn_next)
        
        
        self.btn_play.connect("clicked", self.btn_clicked)
        self.btn_stop.connect("clicked", self.btn_clicked)
        self.btn_prev.connect("clicked", self.btn_clicked)
        self.btn_next.connect("clicked", self.btn_clicked)
        self.btn_pause.connect("clicked", self.btn_clicked)
        
        self.volevent = False

    def btn_clicked(self,widget):        
        if widget == self.btn_next:
            self.cfg.get_backend().next()
        elif widget == self.btn_play:
            self.cfg.get_backend().play()
        elif widget == self.btn_stop:
            self.cfg.get_backend().stop()
        elif widget == self.btn_pause:
            self.cfg.get_backend().pause()
        elif widget == self.btn_prev:
            self.cfg.get_backend().prev()

        
    def state_changed(self,newstate):
        if newstate == State.STOPPED:
            self.btn_stop.set_sensitive(False)
            self.btn_play.set_sensitive(True)
            self.btn_pause.set_sensitive(True)
        elif newstate == State.PAUSED:
            self.btn_stop.set_sensitive(True)
            self.btn_play.set_sensitive(True)
            self.btn_pause.set_sensitive(False)
        else:
            self.btn_stop.set_sensitive(True)
            self.btn_play.set_sensitive(False)
            self.btn_pause.set_sensitive(True)

    def song_changed(self,newplentry):
        self.songlabel.set_label(str(newplentry))
        if newplentry.length > 0:
            self.pos_scale.set_range(0,newplentry.length)
        self.pos_changed(0)

    def pos_changed(self,newPos):
        self.posevent = True
        newPos = int(newPos)
        self.pos_scale.set_value(newPos)
        lbl = format_time(newPos)
        self.timelabel.set_label(lbl)
        self.posevent = False
        
    def random_changed(self,newRand):
        self.random.set_active(newRand)
        
    def repeat_changed(self,newRept):
        self.repeat.set_active(newRept)

    def volume_changed(self,newVolume):
        self.volevent = True
        self.vol_scale.set_value(newVolume)
        self.volevent = False
    
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
        self.pos_scale.connect("value-changed",self.on_pos_change)
        self.pos_scale.set_increments(5,20)
        self.pos_scale.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
        hbox2.add(self.pos_scale)
        vbox.add(hbox2)
        
        #volume,random,repeat
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label("Vol."),False,False,0)
        self.vol_scale = gtk.HScale();
        self.vol_scale.set_range(0,100)
        self.vol_scale.set_property("draw-value",False)
        self.vol_scale.connect("value-changed",self.on_volume_change)
        self.vol_scale.set_increments(5,20)
        self.vol_scale.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
        hbox.add(self.vol_scale)
        
        #random, repeat
        self.random = gtk.CheckButton(label="random")
        hbox.pack_start(self.random,False,False,0)
        self.repeat = gtk.CheckButton(label="repeat")
        hbox.pack_start(self.repeat,False,False,0)
        self.random.connect("toggled",self.on_random)
        self.repeat.connect("toggled",self.on_repeat)
        
        vbox.add(hbox)
        
        return vbox
    
    def on_random(self,widget):
        self.cfg.get_backend().set_random(widget.get_active())
        
    def on_repeat(self,widget):
        self.cfg.get_backend().set_repeat(widget.get_active())
    
    def on_volume_change(self,range):
        if self.volevent == False:
            self.cfg.get_backend().set_volume(range.get_value())
            
    def on_pos_change(self,range):
        if self.posevent == False:
            self.cfg.get_backend().seek(range.get_value())
        