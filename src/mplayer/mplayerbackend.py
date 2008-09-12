from backend import *
import os
import re
from mplayer import MPlayer

from threading import Thread
from pythm import is_numeric
import time



class StateChecker(Thread):
    """
    checks the backend/playing state
    """
    def __init__ (self,backend):
        Thread.__init__(self)
        self.backend = backend
        self.running=True
        self.stopped = False
        
    def run(self):
        while self.running == True:
            #thread logic here
            #print "check"
            time.sleep(1)
            self.backend.checkState()
            
        self.stopped=True


class MplayerBackend(PythmBackend):
    """
        Backend for mplayer control
        Provides basic Player usage and file browsing.
    """
    
    def __init__(self,evthandler):
        PythmBackend.__init__(self,evthandler)
        self.playlist = []
        
        self.endings = ["ogg","mp3"]
        self.filematchers = []
        self.filematchers.append(".*-(?P<artist>.*)-(?P<title>.*)\..*") 
        self.filematchers.append("(?P<artist>.*)-(?P<title>.*)\..*") 
        self.filematchers.append("(?P<title>.*)\..*")
        
        MPlayer.populate()
        self.mplayer = MPlayer()
        self.statecheck = StateChecker(self)
        self.statecheck.start()
        self.currentSong = None
        self.random = False
        self.repeat = False
        self.state = State.STOPPED
    
    def set_volume(self,newVol):
        """sets new volume"""
        self.mplayer.volume(newVol,1)
        self.emit(Signals.VOLUME_CHANGED,newVol)
    
    def set_random(self,rand):
        self.random = rand
        self.emit(Signals.RANDOM_CHANGED,rand)
        
    def set_repeat(self,rept):
        self.repeat = rept
        self.emit(Signals.REPEAT_CHANGED,rept)
    
    
    def play(self, pleid=None):
        """Plays a song from the playlist or starts playing of pleid=None"""
        if self.state == State.STOPPED or pleid is not None:        
            entry = self.playlist[0]
            self.mplayer.loadfile(entry.id)
            entry.length = float(self.mplayer.get_time_length())
            #entry.artist = self.mplayer.get_meta_artist()
            #entry.title = self.mplayer.get_meta_title()
            self.currentSong = entry
            self.emit(Signals.SONG_CHANGED,entry)
        elif self.state == State.PAUSED:
            #toggle pause off
            self.mplayer.pause()
        
        self.set_state(State.PLAYING)
    
    
    def set_state(self,newState):
        self.state = newState
        self.emit(Signals.STATE_CHANGED,newState)
    
    def next(self):
        """Next song in playlist"""
        pass
    
    def prev(self):
        """Previous song in Playlist"""
        pass
    
    def pause(self):
        """pauses playback"""
        pass
    
    def stop(self):
        """stops playback"""
        if self.state != State.STOPPED:
            self.mplayer.stop()
            self.set_state(State.STOPPED)

    
    def browse(self,parentDir=None):
        """
        browses trough the filesystem
        """
        if parentDir is None:
            parentDir = os.path.expanduser("~")
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
        if file.startswith("."):
            return False
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
        tpl = self.getData(fn)
        entry = PlaylistEntry(beId,tpl[0],tpl[1],0)
        self.playlist.append(entry)
        self.emit(Signals.PL_CHANGED,self.playlist)
        
    def getData(self,file):
        """
        returns (artist,title) from regex filename match
        """
        for r in self.filematchers:
            m = re.match(r,os.path.basename(file))
            if(m):
                art = m.group("artist") or ""
                tit = m.group("title")
                return (art,tit)
        return ("",file)
    
    def remove(self,plid):
        """removes entry from pl"""
        pass
    
    def up(self,plid):
        """moves plentry up"""
        pass
    
    def seek(self,pos):
        """seeks to pos in seconds"""
        pass
    
    def shutdown(self):
        self.statecheck.running = False
        while not self.statecheck.stopped:
            time.sleep(0.1)
        self.mplayer.quit()
            
    def checkState(self):
        """
            gets called from StateChecker Thread.
        """
        pos = self.mplayer.get_time_pos()
        #print "Pos: " + str(pos)
        if is_numeric(pos):
            self.emit(Signals.POS_CHANGED, pos)
            
    def populate(self):
        """populates the player"""
        self.set_volume(50)
        self.set_repeat(False)        
        self.set_random(False)

        
        