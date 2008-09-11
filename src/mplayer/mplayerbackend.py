from backend import PythmBackend,PlaylistEntry,BrowserEntry,browserEntryCompare,Signals
import os
import re

class MplayerBackend(PythmBackend):
    """Example backend"""
    
    def __init__(self):
        PythmBackend.__init__(self)
        self.playlist = []
        
        self.endings = ["ogg","mp3"]
        self.filematchers = []
        self.filematchers.append(".*-(?P<artist>.*)-(?P<title>.*)\..*") 
        self.filematchers.append("(?P<artist>.*)-(?P<title>.*)\..*") 
        self.filematchers.append("(?P<title>.*)\..*")
        
        pass
    
    def get_pl(self):
        """returns a list of PlaylistEntries in the current List"""
        return self.playlist
    
    def get_volume(self):
        """volume state"""
        return Volume(0,100,25);
    
    def set_volume(self,newVol):
        """sets new volume"""
        pass
    
    def get_state(self):
        """state of the player"""
        state = State()
        state.pos = 30;
        state.pleid = 1
    
    def play(self, pleid=None):
        """Plays a song from the playlist or starts playing of pleid=None"""
        pass
    
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
        pass
    
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
        entry = PlaylistEntry(1,tpl[0],tpl[1],0)
        self.playlist.append(entry)
        self.emit(Signals.PLAYLIST_CHANGED)
        
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
        pass

        
        