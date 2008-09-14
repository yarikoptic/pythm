from backend import *
import os
import re
import sys
from mplayer import MPlayer
from threading import Thread, Lock

from pythm import is_numeric

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
    
    def __init__(self,evthandler):
        PythmBackend.__init__(self,evthandler)
        
        endings = self.cfg.get("mplayer","endings","ogg,mp3")
        self.endings = endings.lower().split(",")
        
        self.filters  = self.cfg.get_array("mplayer","filters")
        
        self.filematchers = []
        self.filematchers.append(".*-(?P<artist>.*)-(?P<title>.*)\..*") 
        self.filematchers.append("(?P<artist>.*)-(?P<title>.*)\..*") 
        self.filematchers.append("(?P<title>.*)\..*")
        
        self.mplayer = MPlayer()
        
        self.current = None
        self.first = None
        self.last = None
        self.entrydict = {}
        
        self.gotpos = False
        
        self.random = False
        self.repeat = False
        self.state = State.STOPPED
        self.lock = Lock()
    
    def set_volume(self,newVol):
        """sets new volume"""
        print "newvol: "+str(newVol)
        self.mplayer.command("volume",newVol,1)
        self.emit(Signals.VOLUME_CHANGED,newVol)
    
    def set_random(self,rand):
        self.random = rand
        self.emit(Signals.RANDOM_CHANGED,rand)
        
    def set_repeat(self,rept):
        self.repeat = rept
        self.emit(Signals.REPEAT_CHANGED,rept)
    
    
    def play(self, plid=None):
        """Plays a song from the playlist or starts playing of pleid=None"""
        if self.state == State.PAUSED:
            #toggle pause off
            self.mplayer.command("pause")
            self.set_state(State.PLAYING)
        else:
            if plid != None:
                self.choose_song(plid)
            if self.current != None:
                entry = self.current[1]
                self.emit(Signals.SONG_CHANGED,entry)
                self.songend = time.time()
                array = self.mplayer.arraycmd("loadfile","Starting playback...",entry.id)
                self.fill_entry(array, entry)
                
                if entry.length == -1:
                    entry.length = self.mplayer.cmd("get_time_length","ANS_LENGTH")
                self.songend += entry.length
                self.emit(Signals.SONG_CHANGED,entry)
                self.set_state(State.PLAYING)
            else:
                self.set_state(State.STOPPED)    
        
    
    def choose_song(self,plid = None):
        if self.current is None:
            self.current = self.first
            
        if plid != None:
            self.current = self.entrydict[plid]
            
        if self.current != None:
            self.emit(Signals.SONG_CHANGED,self.current[1])
        
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
            self.set_state(State.STOPPED)
        except:
            pass
        self.lock.release()

    def fill_entry(self,array,entry):
        """
        fills entry with track data
        """
        for val in array:
            m = re.match(" Artist\: (?P<value>.*)",val)
            if(m):
                entry.artist = m.group("value").strip()
            m = re.match(" Name\: (?P<value>.*)",val)                
            if(m):
                entry.title = m.group("value").strip()
            
    
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
            if self.filter(file,dir):
                ret.append(BrowserEntry(fullpath,file,dir))
        
        ret.sort(cmp=browserEntryCompare)
        return ret
    
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
        
        fn = os.path.basename(beId)
        tpl = self.get_data(fn)
        entry = PlaylistEntry(beId,tpl[0],tpl[1],-1)
        
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
        
    def emit_pl_changed(self):
        pl = []
        elem = self.first
        while elem is not None:
            pl.append(elem[1])
            elem = elem[2]
            
        self.emit(Signals.PL_CHANGED,pl)
        
    def get_data(self,file):
        """
        returns (artist,title) from regex filename match
        """
        for r in self.filematchers:
            m = re.match(r,os.path.basename(file))
            if(m):
                try:
                    art = m.group("artist").strip()
                except:
                    art = "unknown"
                try:
                    tit = m.group("title").strip()
                except:
                    tit = "unknown"
                return (art,tit)
        return ("",file)
    
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
            self.songend = time.time() + (self.current[1].length - pos)
            self.mplayer.command("seek",pos,2)
    
    def shutdown(self):
        """
        shuts down backend
        """
        PythmBackend.shutdown(self)
    
        self.mplayer.quit()
            
    def check_state(self):
        """
            gets called from StateChecker Thread.
        """
        try:
            self.lock.acquire()
            if self.state == State.PLAYING:
                pos = self.mplayer.cmd("get_time_pos",'ANS_TIME_POS')
                
                if self.current != None:
                    length = self.current[1].length
                #print "Pos: " + str(pos)
                if is_numeric(pos):
                    self.emit(Signals.POS_CHANGED, pos)
                else:
                    if time.time() > self.songend:
                        self.songend = time.time() + 15
                        self.next()
        except:
            print "unexpected error in check_state", sys.exc_info()[0]
        self.lock.release()
            
    def populate(self):
        """populates the player"""
        self.set_volume(80)
        self.set_repeat(False)        
        self.set_random(False)
        self.set_state(State.STOPPED)

        
        