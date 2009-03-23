from pythm.config import PythmConfig
from threading import Thread,Lock
import time
import dbus

class StoppableThread(Thread):
    def __init__ (self):
        Thread.__init__(self)
        self.running = True
        self.stopped = True
    def run(self):
        self.stopped = False
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
        self.backend = backend
        
    def doWork(self):
        time.sleep(0.8)
        if self.backend.is_connected():
            self.backend.check_state()

class PythmBackend(object):
    """Example backend"""
        
    def __init__(self,name):
        """
        initializes a new backend.
        eventhandler is a gui callback function that ensures that 
        the backend functions emit signals in the gui's thread.
        """
        self.name = name
        self.cfg = PythmConfig()
        self.eventhandler = None
        self.initialized = False
        self.quiet = True

	self.sessbus = None
	self.suspendref = None
	self.origlocktime = -1
        self.init_dbus()
        pass
    
    def cb_call_status(self, id, status, props):
        print "Phone call status changed to: " + status

    def init_dbus(self):
        try:
            self.sessbus = dbus.SessionBus()
            obj = self.sessbus.get_object(
		"org.enlightenment.wm.service",
		"/org/enlightenment/wm/RemoteObject",
		introspect=False)
            self.suspendref = dbus.Interface(obj, dbus_interface="org.enlightenment.wm.IllumeConfiguration")
            self.origlocktime = self.suspendref.AutosuspendTimeoutGet()
	    print self.origlocktime
        except Exception, e:
            self.suspendref = None
	    print str(e)
	try:
            #self.sysbus = dbus.SystemBus()
            #self.sysbus = dbus.SessionBus()
            self.sessbus.add_signal_receiver(self.cb_call_status,
                dbus_interface="org.openmoko.qtopia.Phonestatus",
                signal_name="stateChanged",
                path="/Status",
                bus_name="org.openmoko.qtopia.Phonestatus")
        except Exception, e:
	    print str(e)

    def startup(self,handler):
        self.statecheck = StateChecker(self)
        self.initialized = True
        self.eventhandler = handler
        self.statecheck.start()
        return True
    
    def is_started(self):
        return self.initialized
        
    def is_connected(self):
        return not self.quiet
    
    def disconnect(self):
        self.quiet = True
        
    def reconnect(self):
        self.quiet = False
    
        
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
        if self.is_started():
            self.emit(Signals.BROWSER_CHANGED,None,[])
            self.emit(Signals.PL_CHANGED,[])
            self.emit(Signals.STATE_CHANGED,State.DISABLED)
            self.disconnect()
            
            self.initialized = False
            self.quiet = True
            self.statecheck.stop()
    
    def connect(self, signal, callback):
        if not self.cfg.callbacks.has_key(signal):
            self.cfg.callbacks[signal] = []
            
        self.cfg.callbacks[signal].append(callback)
    
    def emit(self, signal, *args):
        """raises callbacks"""
        if not self.quiet:
            if self.cfg.callbacks.has_key(signal):
                for call in self.cfg.callbacks[signal]:
                    self.eventhandler(call, *args)
                
    def populate(self):
        """
        emits signals to populate the gui
        """
        raise NotImplementedError("populate")
    
    def check_state(self):
        """callback of statechecker"""
	"""pls see mplayerbackend for an implementation --ptt"""
        pass
    
    def browse_up(self,current_dir):
        """
        the browse list parent dir of current dir
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
    # Signal args: current_dir, browselist
    BROWSER_CHANGED = "browser_changed"
    # COMMAND_STATE, true oder false
    COMMAND_STATE = "command_state"
        
    
class State:
    PLAYING = 0
    PAUSED = 1
    STOPPED = 2
    DISABLED = 3


class PlaylistEntry:
    def __init__(self, id, artist, title, album, track, cover):
        self.id = id
        self.artist = artist
        self.title = title
        self.album = album
        self.track = track
        self.cover = cover
        self.length = -1
        
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


    
class HelperThread(Thread):
    
    def __init__(self,backend):
        Thread.__init__(self)
        self.setDaemon(True)
        self.backend = backend;
        self.cmds = []
        self.lock = Lock()
        
    def add_cmd(self,*args):
        try:
            self.lock.acquire()
            if len(self.cmds) == 0:
                self.backend.emit(Signals.COMMAND_STATE,False)
                
            self.cmds.append(args)
        finally:
            self.lock.release()
        
    def run(self):
        while True:
            time.sleep(0.1)
            cmd = None
            try:
                self.lock.acquire()
                if len(self.cmds) > 0:
                    cmd = self.cmds.pop()
            except Exception, e:
                print "error executing:" + str(e)
            finally:
                self.lock.release()
            if cmd != None:
                try:                        
                    #print "executing "+cmd[0]
                    args = cmd[1]
                    getattr(self.backend,cmd[0])(*args)
                    #print "executed "+cmd[0]
                except Exception, e:
                    print "error executing:" + str(e)
                finally:
                    if len(self.cmds) == 0:
                        self.backend.emit(Signals.COMMAND_STATE,True);

class ThreadedBackend():
    """
    Backend that threads the function calls from the gui
    """
    def __init__(self,backend):
        self.thread = HelperThread(backend)
        self.backend = backend
        self.thread.start()
        self.directcommands = ["startup","shutdown","connect",
                               "reconnect","disconnect","name",
                               "is_started","is_connected"]
        
    def __getattr__(self,*args):
        cmd = args[0]
        if cmd.startswith("__") or cmd in self.directcommands:
            return getattr(self.backend,*args)
        return lambda *args: self.func(cmd,args)
    
    def func(self,*args):
        self.thread.add_cmd(*args)
        
        
        
class DummyBackend():
    """
    dummy backend that connects all signals
    """
    def __init__(self):
        self.cfg = PythmConfig()
        
    def __getattr__(self,*args):
        return lambda *args: self.func(args)
    
    def func(self,*args):
        pass
    
    def connect(self, signal, callback):
        if not self.cfg.callbacks.has_key(signal):
            self.cfg.callbacks[signal] = []
            
        self.cfg.callbacks[signal].append(callback)

    
