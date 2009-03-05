# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the pythm for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
""" TODO: Module description """

from pythm.config import PythmConfig
from threading import Thread,Lock
from pythm.constants import *
import time
import logging
import dbus
import e_dbus
import ecore

UPDATE_TIME = 0.1 # Time between update loops.
RESUME_FROM_PHONE_TIME = 2 # Time before resuming after phone call suspend.

logger = logging.getLogger("pythm")
logging.basicConfig(level    = logging.CRITICAL,
            format   = '%(asctime)s %(levelname)s %(message)s',
            filename = '/tmp/pythm.log',
            filemode = 'w')
logger.setLevel(logging.DEBUG)

class StoppableThread(Thread):
    def __init__ (self):
        Thread.__init__(self)
        self.running = True
        self.stopped = True

    def run(self):
        self.stopped = False
        self.elapsedTime = 0.0
        self.timeStart = time.time()
        ecore.timer_add(UPDATE_TIME, self.update)
        ecore.main_loop_begin()

        # DMR old way of doing it.
        """
        while self.running == True:
        timeStart = time.time()
            self.do_work()
        self.elapsedTime = time.time() - timeStart
        """
        self.stopped = True

    def update(self):
        self.elapsedTime = time.time() - self.timeStart
        self.timeStart = time.time()
        self.do_work()
        ecore.timer_add(UPDATE_TIME, self.update)

    def stop(self):
        ecore.main_loop_quit()
        self.running = False
        #while self.stopped == False:
            #time.sleep(0.1)

"""
" checks the backend/playing state
"""
class StateChecker(StoppableThread):
    def __init__ (self,backend):
        StoppableThread.__init__(self)
        self.backend = backend

    """
    " Performs time based processing.
    """
    def do_work(self):
        # DMR old way of doing it.
        #time.sleep(0.1)

        # Must be connected to a back-end to bother performing
        # these actions.
        if (self.backend.is_connected()):
            self.backend.check_state(self.elapsedTime)

            # Watch for being asked to asynchronously restart playback
            # after pause from incoming phone call.
            if (self.backend.resumePhoneTimer > 0):
                self.backend.resumePhoneTimer -= self.elapsedTime
                if (self.backend.resumePhoneTimer <= 0):
                    self.backend.resume_from_phone()

"""
" Base class for all playing backends.
"""
class PythmBackend(object):

    """
    " initializes a new backend.
    " eventhandler is a gui callback function that ensures that
    " the backend functions emit signals in the gui's thread.
    """
    def __init__(self,name):
        self.name = name
        self.cfg = PythmConfig()
        self.eventhandler = None
        self.initialized = False
        self.quiet = True
        self.sysbus = None
        self.sesbus = None
        self.mainloop = None
        self.state = State.DISABLED
        self.oldLockTime = -1	# Original enlightenment susepend time.
        self.suspendRef = None	# Reference to dbus suspend disabling setting.
        self.suspendDisabled = False  # Remember if we already disabled suspend.
        self.resumePhoneTimer = 0.0

        self.init_dbus()

        pass

    """
    " Begin processing.
    " Start main thread.
    """
    def startup(self,handler):
        self.statecheck = StateChecker(self)
        self.initialized = True
        self.eventhandler = handler
        self.statecheck.start()
        return True

    """
    " Initialze hooks into dbus.
    " Gets the session and system bus references and adds
    " a callback to watch for incoming calls.
    """
    def init_dbus(self):
        try:
            self.mainLoop   = e_dbus.DBusEcoreMainLoop()
            self.sysbus     = dbus.SystemBus(mainloop=self.mainLoop)
            self.sesbus     = dbus.SessionBus(mainloop=self.mainLoop)

            if (self.sysbus == None or self.sesbus == None):	return

            # Add a listener for changes to the GSM interface.
            self.sysbus.add_signal_receiver(self.cb_call_status,
                dbus_interface="org.freesmartphone.GSM.Call",
                signal_name="CallStatus",
                path="/org/freesmartphone/GSM/Device",
                bus_name="org.freesmartphone.ogsmd")

            self.init_suspend_disable()

        except dbus.DBusException, e:
            logger.warn("Could not connect to dbus.")

    """
    " Initialize the dbus reference for disabling suspend when playing.
    """
    def init_suspend_disable(self):
        # If not set in the config file to explicitly no disable suspend while
        # plaing, setup the interface to do so.
        noSuspend = self.cfg.get(CFG_SECTION_PYTHM, CFG_SETTING_NOSUSPEND, "true")
        iface = self.cfg.get(CFG_SECTION_PYTHM, CFG_SETTING_SUSPENDIFACE, SUSPEND_IFACE_FSO)
        # Keep the default value of None in self.suspendRef as a way of knowing if this
        # setting was disabled.
        if (noSuspend != "true"): return;

        try:
            # Enlightenment dbus.
            if (iface == SUSPEND_IFACE_E):
                dbusName = "org.enlightenment.wm.service"
                dbusPath = "/org/enlightenment/wm/RemoteObject"
                dbusIface = "org.enlightenment.wm.IllumeConfiguration"
                obj = self.sesbus.get_object(dbusName, dbusPath, introspect=False)
                self.suspendRef = dbus.Interface(obj, dbus_interface=dbusIface)
                self.oldLockTime = self.suspendRef.AutosuspendTimeoutGet()
            # Frameworkd dbus.
            else:
                dbusName = "org.freesmartphone.ousaged"
                dbusPath = "/org/freesmartphone/Usage"
                dbusIface = "org.freesmartphone.Usage"
                obj = self.sysbus.get_object(dbusName, dbusPath, introspect=False)
                self.suspendRef = dbus.Interface(obj, dbus_interface=dbusIface)

        except Exception, e:
            self.suspendRef = None
            logger.error("Failed to obtain ref to suspend disable configuration: %s" % e)

    """
    " Sets the suspend mode of the device to no suspend based on the current
    " playback state.
    """
    def set_suspend_disable(self):
        try:
            # Disable suspend on play not enabled.
            if (self.suspendRef == None): return

            iface = self.cfg.get(CFG_SECTION_PYTHM, CFG_SETTING_SUSPENDIFACE, SUSPEND_IFACE_FSO)

            # Set to no suspend.
            if (self.state == State.PLAYING and not self.suspendDisabled):
                if (iface == SUSPEND_IFACE_E):
                    self.suspendRef.AutosuspendTimeoutSet(0)
                else:
                    self.suspendRef.RequestResource("CPU");

                self.suspendDisabled = True

            # Restore old setting.
            elif (self.state > -1 and self.suspendDisabled):
                if (iface == SUSPEND_IFACE_E):
                    self.suspendRef.AutosuspendTimeoutSet(int(self.oldLockTime))
                else:
                    self.suspendRef.ReleaseResource("CPU");

                self.suspendDisabled = False

        except Exception,e:
            logger.debug("Unable to set no suspend: %s" % e)

    """
    " Callback for when the GSM call state changes.
    " when we get a call, pause playback if playing.
    " When call ends, resume play back if paused from playing.
    """
    def cb_call_status(self, id, status, props):
        logger.debug("Phone call status changed to: %s." % status)

        if status == "outgoing" or status == "active" or status == "incoming":
            logger.debug("Initiating playback pause for phone call state.")

        if (self.state == State.PLAYING):
            self.pause_for_phone()

        else:
            if (self.state == State.PAUSED_PHONE):
                self._resume_from_phone()

    """
    " Sets our state and emits a state changed signal.
    """
    def set_state(self, newState):
        if (self.state == newState): return

        self.state = newState
        self.set_suspend_disable()
        self.emit(Signals.STATE_CHANGED, newState)

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

    """
    " Called to pause playback when the phone is activated.
    """
    def pause_from_phone(self):
        raise NotImplementedError()

    """
    " Called to resume playing when a phone call ends.
    """
    def resume_from_phone(self):
        raise NotImplementedError()

    """
    " Private method to begin the resuming from a call process.
    " Initiate a timed resume to give the system a chance to
    " release the audio from the phone call.
    """
    def _resume_from_phone(self):
        self.resumePhoneTimer = RESUME_FROM_PHONE_TIME

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

            self.state = State.STOPPED
            # Restore suspend state on shutdown.
            self.set_suspend_disable()

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

    def check_state(self,elapsedTime):
        """callback of statechecker"""
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

"""
" Posible play states.
"""
class State:
    PLAYING = 0
    PAUSED = 1
    STOPPED = 2
    DISABLED = 3
    PAUSED_PHONE = 4

"""
" Possible directions of track advancement.
"""
class PlayDirection:
    CURRENT = 0
    FORWARD = 1
    BACKWARD = 2
    RANDOM = 3

class PlaylistEntry:
    def __init__(self, id, artist, title, length, album, cover):                         
        self.id = id
        self.artist = artist                                 
        self.title = title                                                   
        self.length = length                                                
        self.album = None
        self.cover = None

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


