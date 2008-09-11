
class PythmBackend(object):
    """Example backend"""
        
    def __init__(self):
        self.callbacks = {}
        pass
    
    def get_pl(self):
        """returns a list of PlaylistEntries in the current List"""
        entry = PlaylistEntry(1,"paul","song",666)
        return [entry,entry]
    
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
        """browses trough the library/fs"""
        ret = []
        ret.append(BrowseEntry("a","aDir",True))
        ret.append(BrowseEntry("b","aFile"))
        return ret
    
    def add(self,beId):
        """adds a browseEntry to the pl"""
        pass
    
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
    
    def connect(self,signal,callback):
        if not self.callbacks.has_key(signal):
            self.callbacks[signal] = []
            
        self.callbacks[signal].append(callback)
    
    def emit(self,signal):
        """raises callbacks"""
        if self.callbacks.has_key(signal):
            for call in self.callbacks[signal]:
                call()
                
class Signals:
    """
    Signals emitted by Backend...
    """
    PLAYLIST_CHANGED = "playlist_changed"
        
    
class State:
    PLAYING = 0
    PAUSED = 1
    STOPPED = 2
    
    def __init__(self):
        #position in song
        self.pos = 0
        #playlist id of current song
        self.pleid = 0
        #status
        self.status = State.PLAYING
        
        

class Volume:
    def __init__(self,min,max,current):
        self.min = min
        self.max = max
        self.current = current


class PlaylistEntry:
    def __init__(self,id,artist,title,length):
        self.id = id
        self.artist = artist
        self.title = title
        self.length = length
        
class BrowserEntry:
    def __init__(self,id,caption,isDir=False):
        self.id = id
        self.caption = caption
        self.isDir = isDir
        
        
def browserEntryCompare(e1,e2):
    """
    Compares two BrowserEntries
    """
    if e1.isDir and not e2.isDir:
        return -1
    elif not e1.isDir and e2.isDir:
        return 1
    
    return cmp(e1.caption,e2.caption)