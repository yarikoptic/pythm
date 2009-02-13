# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the pythm for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
""" TODO: Module description """

import pygtk
pygtk.require('2.0')
import gtk

from page import Page
from pythm.backend import Signals,State
from pythm.functions import format_time
from gtkhelper import ImageButton

class PagePlay(Page):
    def __init__(self):
	self.duration = 0.0	  # Druation of current song.
	self.doPosUpdates = True  # Set song position from backend in slider.

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
	
	self.duration = newplentry.length
        self.pos_changed(0)

    def pos_changed(self,newPos):
        self.posevent = True
        newPos = int(newPos)
	
	# Set the new value in the controls.
	if (self.doPosUpdates):
            self.pos_scale.set_value(newPos)
	self.set_times_label(newPos)
        self.posevent = False

    def random_changed(self,newRand):
        self.random.set_active(newRand)
        
    def repeat_changed(self,newRept):
        self.repeat.set_active(newRept)

    def volume_changed(self,newVolume):
        self.volevent = True
        self.vol_scale.set_value(newVolume)
        self.volevent = False

    """
    " Set the times label string based on current and
    " total duration.
    """
    def set_times_label(self, position):
	lbl = format_time(position) + " / " + format_time(self.duration)
	self.timelabel.set_label(lbl)
    
    def content(self):
        #track info
        vbox = gtk.VBox()
        self.songlabel = gtk.Label("")
        vbox.pack_start(self.songlabel,True,True,0)
        self.timelabel = gtk.Label("0:00 / 0:00")
        vbox.pack_start(self.timelabel,True,True,0)
        
        #pos slider
        hbox2 = gtk.HBox()
	hbox2.set_border_width(20)
        #hbox2.pack_start(gtk.Label("Pos."),False,False,0)
        self.pos_scale = gtk.HScale();
        self.pos_scale.set_property("draw-value",False)
	self.pos_scale.set_value_pos(1)
	self.pos_scale.connect("button-press-event", self.on_pos_press)
	self.pos_scale.connect("button-release-event", self.on_pos_release)
        self.pos_scale.connect("value-changed",self.on_pos_change)
        self.pos_scale.set_increments(5,10)
        self.pos_scale.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
        hbox2.add(self.pos_scale)
        vbox.add(hbox2)

        #volume,random,repeat
        hbox = gtk.HBox()
	hbox.set_border_width(10)
        hbox.pack_start(gtk.Label("Vol."),False,False,0)
        self.vol_scale = gtk.HScale();
        self.vol_scale.set_range(50,100)
        self.vol_scale.set_property("draw-value",True)
	self.vol_scale.set_digits(0)
	self.vol_scale.set_value_pos(1)
        self.vol_scale.connect("value-changed",self.on_volume_change)
        self.vol_scale.set_increments(1,2)
        self.vol_scale.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
        hbox.add(self.vol_scale)
        vbox.add(hbox)
                
        #random, repeat
        hbox3 = gtk.HBox()
        self.random = gtk.CheckButton(label="random")
        hbox3.pack_start(self.random,True,False,0)
        self.repeat = gtk.CheckButton(label="repeat")
        hbox3.pack_start(self.repeat,True,False,0)
        self.random.connect("toggled",self.on_random)
        self.repeat.connect("toggled",self.on_repeat)
        
        vbox.add(hbox3)
        
        return vbox
    
    def on_random(self,widget):
        self.cfg.get_backend().set_random(widget.get_active())
        
    def on_repeat(self,widget):
        self.cfg.get_backend().set_repeat(widget.get_active())
    
    def on_volume_change(self,range):
        if self.volevent == False:
            self.cfg.get_backend().set_volume(range.get_value())
            

    """
    " Event when the position slider is touched.
    " Set a flag to ignore position updates from the backend.
    " Thise makes using the control easier.
    """
    def on_pos_press(self, widget, event):
	self.doPosUpdates = False
    
    """
    " Event when the position slider is released.
    " Release position update ignore.
    """
    def on_pos_release(self, widget, event):
	self.doPosUpdates = True

    def on_pos_change(self,range):
        if self.posevent == False:
            self.cfg.get_backend().seek(range.get_value())
        