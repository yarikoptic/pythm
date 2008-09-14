import mpdlib2 
from pythm.backend import *
import os
import sys
import traceback

class MpdBackend(PythmBackend):
    """Example backend"""
        
    def __init__(self, eventhandler):
        """
        initializes a new backend.
        eventhandler is a gui callback function that ensures that 
        the backend functions emit signals in the gui's thread.
        """

        PythmBackend.__init__(self,eventhandler)
        self.random = None
        self.repeat = None
        self.playlistid = None
        self.playlist = []
        self.volume = None
        self.state = None
        self.song = None
        try:
            mpd_host = self.cfg.get("mpd","host","localhost")
            mpd_port = self.cfg.get("mpd","port","6600")
            mpd_password = self.cfg.get("mpd","pass",None)
            
            self.mpd = mpdlib2.connect(host=mpd_host, port=mpd_port, password=mpd_password)
        except Exception,e:
            self.mpd = None
            print "could not connect to mpd server: "+str(e)
        
        
    def set_volume(self, newVol):
        """sets new volume"""
        self.mpd.setvol(int(newVol))
        
    def update_volume(self,newVol):
        if self.volume != newVol:
            self.volume = newVol
            self.emit(Signals.VOLUME_CHANGED,newVol)
        
    def set_repeat(self, rep):
        """sets new repeat"""
        if(rep):
            self.mpd.repeat(1)
        else:
            self.mpd.repeat(0)
        
    def update_repeat(self, repeat):
        if self.repeat != repeat:
            self.repeat = repeat
            self.emit(Signals.REPEAT_CHANGED,repeat)
            
    def set_random(self, rand):
        """sets new random"""
        if(rand):
            self.mpd.random(1)
        else:
            self.mpd.random(0)
        
    def update_random(self, rand):
        if self.random != rand:
            self.random = rand
            self.emit(Signals.RANDOM_CHANGED,rand)
    
    def play(self, plid=None):
        """Plays a song from the playlist or starts playing of playlist"""
        if plid is None:
            self.mpd.play()
        else:
            self.mpd.playid(plid)
        
    
    def next(self):
        """Next song in playlist"""
        self.mpd.next()
    
    def prev(self):
        """Previous song in Playlist"""
        self.mpd.previous()
    
    def pause(self):
        """pauses playback"""
        if self.state == State.PAUSED:
            arg = 0
        else:
            arg = 1
        self.mpd.pause(arg)
    
    def stop(self):
        """stops playback"""
        self.mpd.stop()
    
    def browse(self, parentDir=None):
        """browses trough the library/fs - returns a list of BrowseEntries."""
        #lsinfo command
        if parentDir is None:
            lsinfo = self.mpd.lsinfo()
        else:
            lsinfo = self.mpd.lsinfo(parentDir)
        ret = []
        if parentDir != None and parentDir !="":
            ret.append(BrowserEntry(os.path.split(parentDir)[0],"..",True))
        
        for elem in lsinfo:
            #print elem
            #print "==="
            dir = elem["type"] == "directory"
            fn = elem[elem["type"]]
            name = os.path.basename(fn)
            art = ""
            if elem.has_key("artist"):
                art = elem["artist"]
            tit =""
            if elem.has_key("title"):
                tit = elem["title"]
            if not(tit == "" or art == ""):
                if art == "":
                    name = tit
                elif tit == "":
                    name = art
                else:
                    name = art + " - " + tit
            ret.append(BrowserEntry(fn,name,dir))
            
        return ret
    
    def add(self, beId):
        """adds a browseEntry to the pl"""
        self.mpd.add(beId)
    
    def remove(self, plid):
        """removes entry from pl"""
        self.mpd.deleteid(plid)
        self.check_state()
    
    def up(self, plid):
        """moves plentry up"""
        idx = self.get_plid_index(plid)
        if idx != None:
            if idx > 0:
                swapid = self.playlist[idx - 1].id
                self.mpd.swapid(plid,swapid)
                self.check_state()
                
    
    def down(self, plid):
        """moves plentry down"""
        idx = self.get_plid_index(plid)
        if idx != None:
            if idx+1 < len(self.playlist):
                swapid = self.playlist[idx + 1].id
                self.mpd.swapid(plid,swapid)
                self.check_state()

    
    def get_plid_index(self,plid):
        """
        gets index of plid in pl
        """
        i = 0
        for e in self.playlist:
            if e.id == plid:
                return i
            i += 1
        return None
                
    
    def seek(self, pos):
        """seeks to pos in seconds"""
        self.mpd.seek(self.song,int(pos))
    
    def shutdown(self):
        PythmBackend.shutdown(self)
        try:
            self.mpd.close()
        except:
            pass
        
    def update_str_state(self,state):
        if state == "play":
            s = State.PLAYING
        elif state =="pause":
            s = State.PAUSED
        elif state == "stop":
            s = State.STOPPED
        if self.state != s:
            self.state = s
            self.emit(Signals.STATE_CHANGED,s)
            
    def update_song(self,songid):
        if self.song != songid:
            try:
                dict = self.mpd.currentsong()
                plentry = self.get_entry(dict)
                if plentry:
                    self.song = songid
                    self.emit(Signals.SONG_CHANGED,plentry)
            except:
                print e
            
    def update_playlist(self,plid):
        if self.playlistid != plid:
            pl = self.mpd.playlistinfo()
            self.playlistid = plid
            ret = []
            for item in pl:
                e = self.get_entry(item)
                if e:
                    ret.append(e)
            self.emit(Signals.PL_CHANGED,ret)
            self.playlist = ret
    
    def get_entry(self,dict):
        try:
            id = int(dict["id"])
            art = ""
            if dict.has_key("artist"):
                art = dict["artist"]
            tit =""
            if dict.has_key("title"):
                tit = dict["title"]
            if tit == "" and art == "":
                tit = os.path.basename(dict["file"])
            tim = int(dict["time"])
            return PlaylistEntry(id,art,tit,tim)
        except:
            print "get_entry: ", dict
            return None
                
    def populate(self):
        """
        emits signals to populate the gui
        """
        self.check_state()
            
    def check_state(self):
        try:
            if self.mpd != None:
                status = self.mpd.status()
                if status.has_key("random"):
                    self.update_random(int(status["random"])==1)                
                if status.has_key("repeat"):
                    self.update_repeat(int(status["repeat"])==1)                
                if status.has_key("volume"):
                    self.update_volume(int(status["volume"]))                
                if status.has_key("state"):
                    self.update_str_state(status["state"])                
                if status.has_key("song"):
                    self.update_song(int(status["song"]))
                if status.has_key("time"):
                    pos = int(status["time"].split(":")[0])
                    self.emit(Signals.POS_CHANGED, pos)
                if status.has_key("playlist"):
                    self.update_playlist(status["playlist"])
        except Exception,e:
            traceback.print_exc()

                
                