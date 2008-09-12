
class PythmBackend(object):
    """Example backend"""
        
    def __init__(self, eventhandler):
        """
        initializes a new backend.
        eventhandler is a gui callback function that ensures that 
        the backend functions emit signals in the gui's thread.
        """
        self.callbacks = {}
        self.eventhandler = eventhandler
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
        raise NotImplementedError()
    
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
        return str(self.artist) + " - " + str(self.title)
        
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