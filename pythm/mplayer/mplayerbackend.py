from pythm.backend import *
import os
import re
import sys
from mplayer import MPlayer
from threading import Thread, Lock

from pythm.functions import is_numeric

import time

        
class InfoRetriever(StoppableThread):
    def __init__(self):
        StoppableThread.__init__(self,backend)
        self.backend = backend
        self.work = []
        pass
    def add(self,entry):
        self.work.append(entry)
        
    def doWork(self):
        time.sleep(1)
        if len(self.work) > 0:
            for entry in self.work:
                pass
        

         

class MplayerBackend(PythmBackend):
    """
        Backend for mplayer control
        Provides basic Player usage and file browsing.
    """
    
    def __init__(self):
        PythmBackend.__init__(self,"mplayer")

    def startup(self,handler):
        try:
            self.lock = Lock()
                            
            self.current = None
            self.first = None
            self.last = None
            self.entrydict = {}
            
            self.gotpos = False
            
            self.random = False
            self.repeat = False
            self.state = State.STOPPED
            
            path = self.cfg.get("mplayer","path",None)
            renice = self.cfg.get("mplayer","renice",None)
            self.mplayer = MPlayer(path,renice)
            endings = self.cfg.get("mplayer","endings","ogg,mp3")
            self.endings = endings.lower().split(",")
            
            self.filters  = self.cfg.get_array("mplayer","filters")
            
            return PythmBackend.startup(self,handler)
        except Exception,e:
            print "could not start mplayer: "+str(e)            
            return False
    
    def set_volume(self,newVol):
        """sets new volume"""
        self.mplayer.command("volume",newVol,1)
        self.emit(Signals.VOLUME_CHANGED,newVol)
    
    def set_random(self,rand):
        self.random = rand
        self.emit(Signals.RANDOM_CHANGED,rand)
        
    def set_repeat(self,rept):
        self.repeat = rept
        self.emit(Signals.REPEAT_CHANGED,rept)
    
    
    def play(self, plid=None):
        """Plays a song from the playlist or starts playing of plid=None"""
        if self.state == State.PAUSED:
            #toggle pause off
            self.mplayer.command("pause")
            self.set_state(State.PLAYING)
        else:
            if plid != None:
		#i'm already in play loop, if i go on through choose_song, play loops...
                #self.choose_song(plid)
                self.current = self.entrydict[plid]
            if self.current != None:
                entry = self.current[1]
		#XXX ptt song_changed is emitted a lot of times...
                ####self.emit(Signals.SONG_CHANGED,entry)
                self.mplayer.cmd("loadfile '" + entry.id.replace('\'', '\\\'') +"'", "======")
		self.get_meta_data(entry.id)
                entry.length = self.mplayer.cmd("get_time_length","ANS_LENGTH")
                self.emit(Signals.SONG_CHANGED,entry)
                self.set_state(State.PLAYING)
            else:
                self.set_state(State.STOPPED)    
        
    
    def choose_song(self,plid = None):
        if self.current is None:
            self.current = self.first
            
        if plid != None:
            self.current = self.entrydict[plid]
            
	#XXX ptt song_changed is emitted a lot of times...
	#if self.current != None:
	#    self.emit(Signals.SONG_CHANGED,self.current[1])
        
        if self.state == State.PAUSED:
            self.stop()
        
        if self.state == State.PLAYING:
            self.play()
        
    
    def set_state(self,newState):
        self.state = newState
        self.emit(Signals.STATE_CHANGED,newState)
    
    def next(self):
        """Next song in playlist"""
        if self.current == None:
            self.choose_song()
        else:
            if self.current[2] != None:
                self.choose_song(self.current[2][1].id)
            elif self.repeat:
                self.choose_song(self.first[1].id)
    
    def prev(self):
        """Previous song in Playlist"""
        if self.current != None:
            if self.current[0] != None:
                self.choose_song(self.current[0][1].id)
            elif self.repeat:
                self.choose_song(self.last[1].id)
    
    def pause(self):
        """pauses playback"""
        try:
            self.lock.acquire()
            if self.state == State.PLAYING:
                self.mplayer.command("pause")
                self.set_state(State.PAUSED)
            else:
		self.play()
        except:
            pass
        self.lock.release()
    
    def stop(self):
        """stops playback"""
        try:
            self.lock.acquire()
            if self.state == State.PLAYING:
                #stop does not work??! fake here
                self.mplayer.command("pause")
		#then resets to start of playlist
	        self.current = self.first
            self.set_state(State.STOPPED)
        except:
            pass
        self.lock.release()

    def browse(self,parentDir=None):
        """
        browses trough the filesystem
        """
        if parentDir is None:
            parentDir = os.path.expanduser(self.cfg.get("mplayer","musicdir","~"))
        ret = []        
        
        if parentDir != "/":
            ret.append(BrowserEntry(os.path.split(parentDir)[0],"..",True))
                        
        for file in os.listdir(parentDir):
            dir = False
            fullpath = os.path.join(parentDir,file)
            if os.path.isdir(fullpath):
                dir = True
	    try:
                fullpath = unicode(fullpath,sys.getfilesystemencoding()).encode("utf-8")
	    except:
		pass
            
            if self.filter(file,dir):
                ret.append(BrowserEntry(fullpath,file,dir))
        
        ret.sort(cmp=browserEntryCompare)
        self.emit(Signals.BROWSER_CHANGED,parentDir,ret)
    
    def filter(self,file,dir):
        """
        filters out private files and files with wrong endings.
        """
        for filter in self.filters:
            try:
                if re.match(filter,file):
                    return False
            except:
                pass
            
        if dir:
            return True
        for e in self.endings:
            if file.lower().endswith("."+e):
                return True;
        return False
    
    
    def add(self,beId):
        """
        adds a browseEntry to the pl
        """
        tpl = self.get_meta_data(beId)
        entry = PlaylistEntry(beId,tpl[0],tpl[1],tpl[2],tpl[3],tpl[4])
        
        if self.first == None:
            self.first = [None,entry,None]
            self.current = self.first
            self.last = self.first
        else:
            oldlast = self.last
            newlast = [oldlast,entry,None]
            oldlast[2] = newlast
            self.last = newlast
        
        self.entrydict[entry.id] = self.last
        
        self.emit_pl_changed()

	#XXX ptt song_changed is emitted a lot of times...
	#but here i refresh '>' indicator, whould be corrected
	#TODO refres only ref '>' status of song
	if self.current is not None and self.state != State.STOPPED:
	    self.emit(Signals.SONG_CHANGED,self.current[1])
        
    def emit_pl_changed(self):
        pl = []
        elem = self.first
        while elem is not None:
            pl.append(elem[1])
            elem = elem[2]
            
        self.emit(Signals.PL_CHANGED,pl)
        
# -----get meta_data with mutagen-----------------------

    def get_meta_data(self, file):
	import mutagen, mutagen.id3
        try:
	    id3 = mutagen.id3.ID3(file, translate=False)
	    art = id3.get('TPE1')
	    tit = id3.get('TIT2')
	    alb = id3.get('TALB')
	    trk = id3.get('TRCK')
            if self.cfg.get("mplayer","coverart",'True') == 'True':
	        pic = id3.getall('APIC')
	    else:
	        pic = None
        except:
            return ("",os.path.basename(file),"","",None)
	
        return (art,tit,alb,trk,pic)
    
# ---------------------------------------------------

    def remove(self,plid):
        """removes entry from pl"""
        tpl = self.entrydict[plid]
        
        if tpl == self.first:
            self.first = tpl[2]
        elif tpl == self.last:
            self.last = tpl[0]
        if tpl == self.current:
            self.current = None
            
        if tpl[0] != None:
            tpl[0][2] = tpl[2]
            
        if tpl[2] != None:
            tpl[2][0] = tpl[0]
            
        self.emit_pl_changed()

	# to update '>' column
	if self.current is not None:
            self.emit(Signals.SONG_CHANGED,self.current[1])
    
    def up(self,plid):
        """moves plentry up"""
        tpl = self.entrydict[plid]
        if tpl != self.first:
            entry = tpl[1]
            tpl[1] = tpl[0][1]
            tpl[0][1] = entry
            self.entrydict[plid] = tpl[0]
            self.entrydict[tpl[1].id] = tpl
            self.emit_pl_changed()
            if tpl == self.current:
                self.current = tpl[0]
            
    def down(self,plid):
        tpl = self.entrydict[plid]
        if tpl != self.last:
            entry = tpl[1]
            tpl[1] = tpl[2][1]
            tpl[2][1] = entry
            self.entrydict[plid] = tpl[2]
            self.entrydict[tpl[1].id] = tpl
            self.emit_pl_changed()
            if tpl == self.current:
                self.current = tpl[2]
        
    
    def seek(self,pos):
        """seeks to pos in seconds"""
        if self.state == State.PLAYING:
            self.mplayer.command("seek",pos,2)
	    #ptt: TODO try to seek in percent:
            ###self.mplayer.command("seek",pos,1)
    
    def shutdown(self):
        """
        shuts down backend
        """
        try:
            self.mplayer.quit()
            PythmBackend.shutdown(self)
        except:
            pass
        
    def browse_up(self,current_dir):
        """
        browses the parent dir of current dir
        """
        if current_dir != "/" and current_dir!=None:
            self.browse(os.path.split(current_dir)[0])
    
    def clear(self):
        """
        clears playlist
        """
	# save playing media
        if self.state != State.STOPPED:
            playing_entry = self.current[1]
	else:
	    playing_entry = None
        self.entrydict = {}
        self.first = None
        self.current = None
        self.last = None
	# restore playing media
	if playing_entry is not None:
            self.add(playing_entry.id)
        self.emit_pl_changed()
	if playing_entry is not None:
            self.emit(Signals.SONG_CHANGED,playing_entry)
    
    def add_dir(self,dir_to_add):
        """
        add a dir to pl
        """
        for file in os.listdir(dir_to_add):
            dir = False
            fullpath = os.path.join(dir_to_add,file)
            if os.path.isdir(fullpath):
                dir = True
            if self.filter(file,dir):
                if dir:
                    self.add_dir(fullpath)
                else:
                    self.add(fullpath)
    
            
    def check_state(self):
        """
            gets called from StateChecker Thread.
        """
        try:
            self.lock.acquire()
	    # ptt dbus
            if self.suspendref is not None:
                if self.state == State.PLAYING:
        	    self.curlocktime = self.suspendref.AutosuspendTimeoutGet()
		    if self.curlocktime > 0: 
		        self.origlocktime = self.curlocktime
               	        self.suspendref.AutosuspendTimeoutSet(0)
	        elif self.origlocktime > -1:
        	    self.suspendref.AutosuspendTimeoutSet(self.origlocktime)
	    # ptt dbus end
            if self.state == State.PLAYING:
                pos = self.mplayer.cmd("get_time_pos",'ANS_TIME_POS')
                #pos = self.mplayer.cmd("get_percent_pos",'ANS_PERCENT_POS')
                
                if self.current != None:
                    length = self.current[1].length
                if is_numeric(pos):
                    self.emit(Signals.POS_CHANGED, pos)
                else:
		    # TODO precache following media file
		    #if length-15 > pos:
		    #  	self.next(True)
                    self.next()
        except:
            print "unexpected error in check_state", sys.exc_info()[0]
        self.lock.release()
            
    def populate(self):
        """populates the player"""
        self.set_volume(90)
        self.set_repeat(False)        
        self.set_random(False)
        self.set_state(State.STOPPED)
        self.emit_pl_changed()
        self.browse()

