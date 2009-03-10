import pygtk
pygtk.require('2.0')
import gtk
import os
import pango

from page import Page
from pythm.backend import Signals,State
from pythm.functions import format_time
from gtkhelper import ImageButton

class PagePlay(Page):
    def __init__(self):
        Page.__init__(self);
        self.cfg.get_backend().connect(Signals.VOLUME_CHANGED,self.volume_changed)
        self.cfg.get_backend().connect(Signals.SONG_CHANGED,self.song_changed)
        self.cfg.get_backend().connect(Signals.POS_CHANGED,self.pos_changed)
        self.cfg.get_backend().connect(Signals.STATE_CHANGED,self.state_changed)
        
        self.btn_prev = ImageButton(gtk.STOCK_MEDIA_PREVIOUS)
        self.btnbox.add(self.btn_prev)
        self.btn_stop = ImageButton(gtk.STOCK_MEDIA_STOP)
        self.btnbox.add(self.btn_stop)
	#ptt
        self.playimg = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
        self.playimg.set_padding(3,15)
        self.pauseimg = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON)
        self.pauseimg.set_padding(3,15)
	self.btn_playpause = gtk.Button()
        self.btn_playpause.set_image(self.playimg)
        self.btnbox.add(self.btn_playpause)
        self.btn_next = ImageButton(gtk.STOCK_MEDIA_NEXT)
        self.btnbox.add(self.btn_next)
        
        self.btn_prev.connect("clicked", self.btn_clicked)
        self.btn_stop.connect("clicked", self.btn_clicked)
        self.btn_playpause.connect("clicked", self.btn_clicked)
        self.btn_next.connect("clicked", self.btn_clicked)
        
        self.volevent = False
	
	#ptt
        self.playimg = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
        self.playimg.set_padding(3,15)
        self.pauseimg = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON)
        self.pauseimg.set_padding(3,15)

    def btn_clicked(self,widget):        
        if widget == self.btn_next:
            self.cfg.get_backend().next()
        elif widget == self.btn_stop:
            self.cfg.get_backend().stop()
        elif widget == self.btn_prev:
            self.cfg.get_backend().prev()
        elif widget == self.btn_playpause:
            self.cfg.get_backend().pause()

        
    def state_changed(self,newstate):
        if newstate == State.STOPPED:
            self.btn_stop.set_sensitive(False)
            self.btn_playpause.set_sensitive(True)
            self.btn_playpause.set_image(self.playimg)
        elif newstate == State.PAUSED:
            self.btn_stop.set_sensitive(True)
            self.btn_playpause.set_image(self.playimg)
        else:
            self.btn_stop.set_sensitive(True)
            self.btn_playpause.set_image(self.pauseimg)

    def song_changed(self,newplentry):
        self.songlabel.set_label(str(newplentry.title))
	# seems not to work right... ?
	self.songlabel.queue_draw()
        self.tpe1label.set_label(str(newplentry.artist))
        self.talblabel.set_label(str(newplentry.album))
	if newplentry.track is not None:
            self.trcklabel.set_label("(" + str(newplentry.track).replace('/', ' of ') + ")")
	    # TODO cut away zeros, eg: xlate 01 to 1
            #self.trcklabel.set_label("(" + str(newplentry.track).replace('/', ' of ').replace(' 0', ' ').strip() + ")")
        if newplentry.length > 0:
            self.pos_scale.set_range(0,newplentry.length)
	    self.totaltime.set_label(" / " + format_time(newplentry.length))

	#load cover art
	if newplentry.cover != None and len(newplentry.cover) > 0:
	    self.coverart.set_property("visible", True)
	    #TODO is there a way to make it less heavy?
	    self.coverart.set_from_pixbuf(self.get_cover_pix(newplentry.cover[0].data))
	    self.talblabel.set_alignment(0, 0.5)
	    self.trcklabel.set_alignment(0, 0.5)
	    self.hboxtm.set_child_packing(self.timelabel,False,True,0,gtk.PACK_START)
	else:
	    self.coverart.set_property("visible", False)
	    self.talblabel.set_alignment(0.5, 0.5)
	    self.trcklabel.set_alignment(0.5, 0.5)
	    self.hboxtm.set_child_packing(self.timelabel,True,True,0,gtk.PACK_START)

        self.pos_changed(0)

    def get_cover_pix(self, data):
	tmp = os.tempnam()
	fd = open(tmp, 'wb')
	fd.write(data)
	fd.flush()
	fd.close()
	pix = gtk.gdk.pixbuf_new_from_file_at_size(tmp, 130, 130)
	os.remove(tmp)
	return pix
	
    def pos_changed(self,newPos):
        self.posevent = True
        newPos = int(newPos)
        self.timelabel.set_label(format_time(newPos))
        self.pos_scale.set_value(newPos)
        self.posevent = False
        
    def volume_changed(self,newVolume):
        self.volevent = True
        self.vol_scale.set_value(newVolume)
        self.volevent = False
    
    def content(self):
	# load preferred fonts
	tagfont = self.cfg.get("pythm","tagfont",None)
        #track info
	#title and artist
        vbox = gtk.VBox()
	#TIT2
        self.songlabel = gtk.Label("")
        vbox.pack_start(self.songlabel,True,True,0)
	#TPE1-2
        self.tpe1label = gtk.Label("")
        vbox.pack_start(self.tpe1label,True,True,0)

	#box with other infos
        hbox0 = gtk.HBox()
	#APIC
	self.coverart = gtk.Image()
        hbox0.pack_start(self.coverart,True,True,0)
	#TALB
        vbox0 = gtk.VBox()
        self.talblabel = gtk.Label("")
        vbox0.pack_start(self.talblabel,True,True,0)
	#TRCK
        self.trcklabel = gtk.Label("")
        vbox0.pack_start(self.trcklabel,True,True,0)
	#TIME
        self.hboxtm = gtk.HBox()
        self.timelabel = gtk.Label("")
	self.timelabel.set_alignment(1,0.5)
        self.hboxtm.pack_start(self.timelabel,False,True,0)
        self.totaltime = gtk.Label("")
	self.totaltime.set_alignment(0,0.5)
        self.hboxtm.pack_start(self.totaltime,True,True,0)

        vbox0.pack_start(self.hboxtm,True,True,0)
        hbox0.pack_start(vbox0,True,True,0)

        vbox.pack_start(hbox0,True,True,0)
	
	# set up fonts
	if tagfont is not None:
	    self.songlabel.modify_font(pango.FontDescription(tagfont))
	    self.tpe1label.modify_font(pango.FontDescription(tagfont))
        
        #volume
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label("Vol"),False,False,0)
        self.vol_scale = gtk.HScale();
	#at 100 it makes a little white noise in background
	#and below 50 is an unusable volume anyway...
        #self.vol_scale.set_range(0,100)
        self.vol_scale.set_range(50,97)
        self.vol_scale.set_property("draw-value",False)
        self.vol_scale.connect("value-changed",self.on_volume_change)
        self.vol_scale.set_increments(2,4)
        self.vol_scale.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
        hbox.pack_start(self.vol_scale,True,True,15)
        vbox.add(hbox)
        
        #pos slider
        hbox2 = gtk.HBox()
        hbox2.pack_start(gtk.Label("Pos"),False,False,0)
        self.pos_scale = gtk.HScale();
	# ptt:
###        self.pos_scale.set_range(0,100)
        self.pos_scale.set_draw_value(0)
        self.pos_scale.connect("value-changed",self.on_pos_change)
        self.pos_scale.set_increments(5,20)
        self.pos_scale.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
        hbox2.pack_start(self.pos_scale,True,True,15)
        vbox.add(hbox2)

        return vbox
    
    def on_volume_change(self,range):
        if self.volevent == False:
            self.cfg.get_backend().set_volume(int(range.get_value()))
            
    def on_pos_change(self,range):
        if self.posevent == False:
            self.cfg.get_backend().seek(int(range.get_value()))
        
