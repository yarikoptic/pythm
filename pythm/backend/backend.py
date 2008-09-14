from pythm.config import PythmConfig
from threading import Thread
import time

class StoppableThread(Thread):
    def __init__ (self):
        self.running = True
        self.stopped = False
    def run(self):
        while self.running == True:
            self.doWork()
        self.stopped = True
        
    def stop(self):
        self.running = False
        while self.stopped == False:
            time.sleep(0.1)

class StateChecker(StoppableThread):
    """
    checks the backend/playing state
    """
    def __init__ (self,backend):
        StoppableThread.__init__(self)
        Thread.__init__(self)
        self.backend = backend
        
    def doWork(self):
        time.sleep(0.8)
        self.backend.check_state()

class PythmBackend(object):
    """Example backend"""
        
    def __init__(self, eventhandler):
        """
        initializes a new backend.
        eventhandler is a gui callback function that ensures that 
        the backend functions emit signals in the gui's thread.
        """
        self.statecheck = StateChecker(self)
        self.cfg = PythmConfig()
        self.callbacks = {}
        self.eventhandler = eventhandler
        self.statecheck.start()
        pass
        
    def set_volume(self, newVol):
        """sets new volume"""
        raise NotImplementedError()       
        
    def set_repeat(self, repeat):
        raise NotImplementedError()
        
    def set_random(self, rand):
        raise NotImplementedError()
    
    def play(self, pleid=None):
        """Plays a song from the playlist or starts playing of playlist"""
        raise NotImplementedError()
    
    def next(self):
        """Next song in playlist"""
        raise NotImplementedError()
    
    def prev(self):
        """Previous song in Playlist"""
        raise NotImplementedError()
    
    def pause(self):
        """pauses playback"""
        raise NotImplementedError()
    
    def stop(self):
        """stops playback"""
        raise NotImplementedError()
    
    def browse(self, parentDir=None):
        """browses trough the library/fs - returns a list of BrowseEntries."""
        raise NotImplementedError()     
    
    def add(self, beId):
        """adds a browseEntry to the pl"""
        raise NotImplementedError("add")
    
    def remove(self, plid):
        """removes entry from pl"""
        raise NotImplementedError()
    
    def up(self, plid):
        """moves plentry up"""
        raise NotImplementedError()
    
    def seek(self, pos):
        """seeks to pos in seconds"""
        raise NotImplementedError()
    
    def shutdown(self):
        self.statecheck.stop()
    
    def connect(self, signal, callback):
        if not self.callbacks.has_key(signal):
            self.callbacks[signal] = []
            
        self.callbacks[signal].append(callback)
    
    def emit(self, signal, *args):
        """raises callbacks"""
        if self.callbacks.has_key(signal):
            for call in self.callbacks[signal]:
                self.eventhandler(call, *args)
                
    def populate(self):
        """
        emits signals to populate the gui
        """
        raise NotImplementedError("populate")
    
    def check_state(self):
        """callback of statechecker"""
        pass
    
    def browse_up(self,current_dir):
        """
        returns the parent dir of current dir
        """
        raise NotImplementedError("browse_up")
    
    def clear(self):
        """
        clears playlist
        """
        raise NotImplementedError("clear")
    
    def add_dir(self,dir):
        """
        add a dir to pl
        """
        raise NotImplementedError("add_dir")
            
                
class Signals:
    """
    Signals emitted by Backend...
    """
    # Signal args: None, reload complete list.
    PL_CHANGED = "playlist_changed"
    # Signal args: new playlistentry
    PL_SONG_ADDED = "playlist_song_added"
    # Signal args: 
    PL_SONG_MOVED = "playlist_song_moved"
    # Signal args: plid of removed song
    PL_SONG_REMOVED = "playlist_song_removed" 
    # Signal args: new Volume, 0-100%
    VOLUME_CHANGED = "volume_changed"
    # Signal args: new Random, boolean
    RANDOM_CHANGED = "random_changed"
    # Signal args: new Repeat, boolean
    REPEAT_CHANGED = "repeat_changed"
    # Signal args: plentry
    SONG_CHANGED = "song_changed"
    # Signal args: new pos in seconds.
    POS_CHANGED = "pos_changed"
    # Signal args: new State
    STATE_CHANGED = "state_changed"
        
    
class State:
    PLAYING = 0
    PAUSED = 1
    STOPPED = 2


class PlaylistEntry:
    def __init__(self, id, artist, title, length):
        self.id = id
        self.artist = artist
        self.title = title
        self.length = length
        
    def __str__(self):
        if len(self.artist) > 0 and len(self.title) > 0:
            return str(self.artist) + " - " + str(self.title)
        elif len(self.title) > 0:
            return self.title
        else:
            return self.artist
        
class BrowserEntry:
    def __init__(self, id, caption, isDir=False):
        self.id = id
        self.caption = caption
        self.isDir = isDir
        
        
def browserEntryCompare(e1, e2):
    """
    Compares two BrowserEntries
    """
    if e1.isDir and not e2.isDir:
        return -1
    elif not e1.isDir and e2.isDir:
        return 1
    
    return cmp(e1.caption, e2.caption)