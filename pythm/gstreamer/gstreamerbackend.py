import os, re, sys, time
import alsaaudio
import ecore.evas
import dbus
import pygst, gst
from pythm.backend import *
from threading import Thread, Lock
#from ID3 import *
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from pythm.functions import is_numeric
from dbus.exceptions import DBusException

# Time (seconds) to wait before polling alsa for the current volume.
ALSA_POLL_TIME = 3
# Name of the alsa mixer channel to contol.
ALSA_MIXER_NM = 'PCM'
# Time between playback time updates.
PLAYBACK_POLL_TIME = 0.8
# Time between async loader thread firing.
ASYNC_POLL_TIME = 1.0
# Time after a song starts that we wait before letting the
# async load thread load a new song.
ASYNC_LOAD_WAIT_TIME = 3.5
# Time to add to elapsed time when determining if song is over.
# This is to get a smooth transition.
NEXT_SONG_FUDGE_TIME = 0.25
# Audio file artist tag name.
TAG_NAME_ARTIST = "artist"
# Audion file album tag name.
TAG_NAME_TITLE = "title"
# File extension for mp3 files.
FILE_EXT_MP3 = ".mp3"
# File extension for ogg files.
FILE_EXT_OGG = ".ogg"
# File extension for flac files.
FILE_EXT_FLAC = ".flac"

"""
" A thread for loading the next track in the background.
" All it does is call async_load_thread in the main backend
" class every so often.
"""
class AsyncLoader(Thread):
    def __init__(self, backend):
	Thread.__init__(self)
	self.backend = backend
	self.running = True	

    def run(self):
	while(self.running):
	    self.backend.async_load_thread(ASYNC_POLL_TIME)
	    time.sleep(ASYNC_POLL_TIME)

"""
" Backend for gstreamer control
" Provides basic Player usage and file browsing.
"""
class GStreamerBackend(PythmBackend):

    """
    " Constructor.
    """
    def __init__(self):
	self.mixer	    = None
	self.lastVolume     = 0
	self.volTimer	    = 0
	self.oldLockTime    = -1
	self.illumeRef	    = None
	self.songTimer	    = 0
	self.songLength	    = 0
	self.pollTimer	    = 0
	self.songChanged    = False	# Flag for async song changed signal emmitt.
	self.players	    = [None, None] # Gstreamer players.
	self.songIds        = [None, None] # ID's of songs currenlty loaded into their respective players.
	self.curPlayer	    = 0		# Current player being played.
	self.threadLoad     = None	# Thread for background loading of next song.
	self.asyncLoadTime  = -1	# Time before async load of next song starts.

        PythmBackend.__init__(self,"gstreamer")

    def startup(self,handler):
        try:
            self.current = None
            self.first = None
            self.last = None
            self.entrydict = {}

            self.gotpos = False

            self.random = False
            self.repeat = False
            self.state = State.STOPPED

	    # Hook into DBUS.
	    self.my_init_dbus() 

	    # Load file browser preferences.
            endings = self.cfg.get("gstreamer","endings","ogg,mp3")
            self.endings = endings.lower().split(",")
            self.filters  = self.cfg.get_array("gstreamer","filters")
            self.filematchers = []
            self.filematchers.append(".*-(?P<artist>.*)-(?P<title>.*)\..*") 
            self.filematchers.append("(?P<artist>.*)-(?P<title>.*)\..*") 
            self.filematchers.append("(?P<title>.*)\..*")

	    # Init gstreamer.
	    self.gstreamer_init()

	    # Start the next song background loader.
	    self.threadLoad = AsyncLoader(self)
	    self.threadLoad.start()

	    # Tell pythm we have loaded successfully.
	    return PythmBackend.startup(self,handler)

        except Exception,e:
            logger.error("Error initializing gstreamer backend: %s " % str(e))
            return False

    """
    " Initialize the gstreamer player.
    """
    def gstreamer_init(self):
	try:
	    # Init gstreamer.                                                                   
            self.players[0] = gst.element_factory_make("playbin", "pythm-player")                   
            self.players[1] = gst.element_factory_make("playbin", "pythm-player")                   
            #fakesink       = gst.element_factory_make("fakesink", "pythm-fakesink")                   
	    # No video so use a fake sink.
            #self.players[0].set_property("video-sink", fakesink)                                  
            #self.players[1].set_property("video-sink", fakesink)                                  

            streamerBus = self.players[0].get_bus()                                                 
            streamerBus.add_signal_watch()                                                      
            streamerBus.connect("message", self.on_player_message, 0)

            streamerBus = self.players[1].get_bus()                                                 
            streamerBus.add_signal_watch()                                                      
            streamerBus.connect("message", self.on_player_message, 1)

	except Exception,e:
	    logger.error("Could not connect to gstreamer: %s" % str(e))

    """
    " Initialize the connection with the alsa system and
    " read the current volume.
    """
    def audio_init(self):
	self.mixer = alsaaudio.Mixer(ALSA_MIXER_NM)
	self.update_volume()   

    """
    " Read the current volume from alsa and set it in the GUI
    " via the volume changed callback.
    """
    def update_volume(self):
	# We have to get a new reference to the mixer each time
	# we call getvolume or it will not be the correct
	# new volume if the volume was changed outside the app.
	mixer = alsaaudio.Mixer(ALSA_MIXER_NM)
	if (mixer != None):
	    vol = mixer.getvolume()[0]
	    if (vol != self.lastVolume):
		self.lastVolume = float(vol)
		self.emit(Signals.VOLUME_CHANGED, self.lastVolume)

    """
    " Set the current hardware volume of the mixer returned
    " by get_mixer().
    """    
    def set_volume(self,newVol):
	if (self.mixer != None):
	    self.mixer.setvolume(int(newVol))
	    self.lastVolume = newVol
            self.emit(Signals.VOLUME_CHANGED,newVol)
    
    """
    " Bind top dbus to do certain things.
    """
    def my_init_dbus(self):
        if (self.sysbus == None or self.sesbus == None):
		return

	# Add a listener for changes to the GSM interface.
	try:
		"""
        	self.sysbus.add_signal_receiver(self.cb_call_status,
                	"CallStatus",
                        "org.freesmartphone.GSM.Call",
                        "org.freesmartphone.ogsmd",
                        "/org/freesmartphone/GSM/Device" )

                #gsmDevice = self.dbus.get_object('org.freesmartphone.ogsmd', '/org/freesmart
                #self.dbusPhone = Interface(gsmDevice, 'org.freesmartphone.GSM.Call')
                #self.dbusPhone.connect_to_signal("Status", self.cbCallStatus)

                #idle = self.dbus.get_object("org.freesmartphone.odeviced", "/org/freesmartph
                #self.dbusIdle = dbus.Interface(idle, "org.freesmartphone.Device.Input")
                #self.dbusIdle.connect_to_signal("Event", self.cbIdle)
		"""
                self.sysbus.add_signal_receiver(self.cb_idle,
                        dbus_interface="org.freesmartphone.Device.IdleNotifier",
                        signal_name="State")
        except DBusException, e:
                logger.error("Failed to add listener for GSM events.")


	# If not set in the config file to explicitly no disable suspend while
	# plaing, setup the interface to do so.
	noSuspend = self.cfg.get("gstreamer", "no_suspend", "true")
	if (noSuspend == "true"):
	    try:
 	        dbusName  	= "org.enlightenment.wm.service"
  	        dbusPath  	= "/org/enlightenment/wm/RemoteObject"
	        dbusIface 	= "org.enlightenment.wm.IllumeConfiguration"
	        eObj 	= self.sesbus.get_object(dbusName, dbusPath, introspect=False)
	        self.illumeRef = dbus.Interface(eObj, dbus_interface=dbusIface)
	        # Get the lock time when the app was started.
	        self.oldLockTime = self.illumeRef.AutosuspendTimeoutGet()
	        #logger.info("Old timeout time: %d" % self.oldLockTime)
	    except:
	        logger.error("Failed to obtain ref to illume configuration: %s" 
			     % sys.exc_info()[1])

    """
    " Sets the suspend mode of the device to no suspend
    " if state = 1 and to the original value if state = 0.
    " This does nothing if the original suspend time was
    " not correctly read.
    """
    def config_set_suspend(self, state):
	# No valid old suspend time.
	if (self.oldLockTime == -1):
	    return
	
	# Restore old suspend time.
	if (state == 0):
	    self.illumeRef.AutosuspendTimeoutSet(int(self.oldLockTime))
	# Set to no suspend.
	else:
	    self.illumeRef.AutosuspendTimeoutSet(0)

	#newTime = self.illumeRef.AutosuspendTimeoutGet()
	#print "New suspend time: " + str(newTime)

    """                                                                
    " Callback for handling dbus on status changed events.
    """                            
    def cb_idle(self, state):                                                 
        #logger.error( "IDLE EVENT = %s" % state)
	if (state == "suspend"):
	    #logger.info("Got suspend state.")
	    #self.stop()
	    pass
	elif (state == "awake"):
	    #logger.info("Got awake state.")
	    #self.gstreamer_init()
	    pass
	    

    """
    " Listen for messages from gstreamer.
    """
    def on_player_message(self, bus, msg, playerId):
	t = msg.type
	player = self.players[playerId]

	#print "*** Message for " + str(playerId) + ": " + str(msg)

	if (t == gst.MESSAGE_STATE_CHANGED):
	    newState = msg.parse_state_changed()[1]
	    #print "*** State changed message: " + str(newState)
		
	    # Actions to performe when the stream is ready.
	    #if (newState == gst.STATE_READY):

	# End of the stream. Play the next song.
	elif (t == gst.MESSAGE_EOS):
	    logger.debug("Got EOS message for player: %i" % playerId)
	    player.set_state(gst.STATE_NULL)
	elif (t == gst.MESSAGE_EOS and playerId == self.curPlayer):
	    #self.next()
	    pass

	# Error message.
	elif (t == gst.MESSAGE_ERROR):
	    err, debug = message.parse_error()
	    logger.error("Gstreamer error %s" % err, debug)

    """
    " Check for a the need to load a new song and then load it into
    " the current inactive player.
    """
    def async_load_thread(self, elapsedTime):
	if (self.asyncLoadTime > 0):
	    self.asyncLoadTime -= elapsedTime
	    if (self.asyncLoadTime < 0): self.asyncLoadTime = 0

	if (self.asyncLoadTime != 0): return
	self.asyncLoadTime = -1

	nextPId = self.get_next_player_id()
	
	if (self.songIds[nextPId] == None):
	    nextSong = self.choose_song(PlayDirection.FORWARD)

	    try:
		logger.debug("Async loading new song into player: %i" % nextPId)
		logger.debug("Async next song is: %s" % str(nextSong[1].id))

		self.players[nextPId].set_state(gst.STATE_NULL)
		self.load_song(nextPId, nextSong[1])
		self.songIds[nextPId] = nextSong[1].id

	    except Exception,e:
		logger.error("Failed to async load song: %s" % str(e))
	
    """
    " Returns the next gstreamer player id.
    " We have two players so the next song can be asynchronously
    " loaded into memory.
    """
    def get_next_player_id(self):
	return (self.curPlayer + 1) % 2

    """
    " Set to play songs in a random order.
    " Fires the random state changed signal.
    """
    def set_random(self,rand):
        self.random = rand
        self.emit(Signals.RANDOM_CHANGED,rand)
       
    """
    " Set to repeat the current song.
    " Fires the repeat state change signal.
    """ 
    def set_repeat(self,rept):
        self.repeat = rept
        self.emit(Signals.REPEAT_CHANGED,rept)
    
    """
    " Load song with the given id into the given gstreamer
    " player. If song is loaded successfully, sets player
    " ready state.
    " Returns true if load successful.
    """
    def load_song(self, playerId, songEntry):
	# Sent the song id of the song to load as empty until
	# it has been successfully loaded.
	self.songIds[playerId] = None

	player = self.players[playerId]

	try:
	    fn = songEntry.id
	    player.set_state(gst.STATE_NULL)
	    player.set_property("uri", "file://" + fn)
	    player.set_state(gst.STATE_PLAYING)

	    if (songEntry.length <= 0):
	    	songEntry.length = self.get_length_retry(self.players[playerId])

	    player.set_state(gst.STATE_PAUSED)

	    # Now remember the song ID.
	    self.songIds[playerId] = fn
	    return True

	except Exception,e:
	    logger.error("Error loading song %s into player %i: %s" % 
		(str(songEntry), playerId, str(e)))
	    return False
    
    """
    " Plays a song from the playlist.
    """
    def play(self, plid=None, stopCurrent = True):
	entryState = self.state

	# Default state to stopped so main update loop will
	# stop drawing somg timer until after new song is
	# loaded.
	self.state = State.STOPPED

	# Disable device suspend while playing.
	self.config_set_suspend(1)
	
	# If paused, simply resume playing.
        if (entryState == State.PAUSED):
	    self.players[self.curPlayer].set_state(gst.STATE_PLAYING)
            self.set_state(State.PLAYING)

	# Check these states only State.PHONE_PAUSED
	# has special handling.
	elif (self.state == State.STOPPED or self.state == State.PLAYING):
	    # If no track given as argument, select the next track.
            if (plid == None):
		songToPlay = self.choose_song()
	    else:
		songToPlay = self.entrydict[plid]

	    logger.debug("Going to play song: %s" % songToPlay[1].id)
	    self.emit(Signals.SONG_CHANGED, songToPlay[1])

	    try:

		if (stopCurrent): self.players[self.curPlayer].set_state(gst.STATE_NULL)

	    	# New song to play is same a current song (e.g., repeat)
	    	# so restart current song without loading.
	    	if (songToPlay[1].id == self.songIds[self.curPlayer]):
		    self.players[self.curPlayer].set_state(gst.STATE_PLAYING)	

	    	# Otherwise, play the selected song.
            	elif (songToPlay != None):
		    player  = None
		    nextPId = self.get_next_player_id()

		    #print "*** current id: " + str(self.curPlayer) + ", next: " + str(nextPId)
		    #print "*** song in next player: " + str(self.songIds[nextPId])

		    # Stop any asynchronous loading while we work.
		    self.asyncLoadTime = -1

		    # First, see if the song that was asynchronously loaded
		    # into the next player is the song we want to play.
		    # In this case, we switch players.
		    if (self.songIds[nextPId] == songToPlay[1].id):
			logger.debug("Song already loaded.")
		    	self.curPlayer = nextPId
			player = self.players[self.curPlayer]
			player.set_state(gst.STATE_PLAYING)

		    # Otherwise, we need to load the new song here.
		    # The current player is kept in this case.
		    # There is no need to switch.
		    else:
			logger.debug("Need to load the song.")
			player = self.players[self.curPlayer]
			
			if (self.load_song(self.curPlayer, songToPlay[1])):
		    	    player.set_state(gst.STATE_PLAYING)

		    # Regardless, set the new current song.
		    self.current = songToPlay

		    # And stimulate the async. loading of the next song.
		    self.songIds[self.get_next_player_id()] = None
		    self.asyncLoadTime = ASYNC_LOAD_WAIT_TIME

		self.songTimer  = 0
		self.songLength = self.current[1].length
            	self.emit(Signals.SONG_CHANGED, songToPlay[1])
                self.set_state(State.PLAYING)

	    except Exception, e:                                           
            	logger.error("Error loading song: %s" % str(e))
		if (player != None):
		    player.set_state(gst.STATE_NULL)


    """
    " Gets the length of a song from a gstreamer player
    " and allows for a few retries.
    """
    def get_length_retry(self, gplayer):
	l	= 0
	retries = 5

	while (retries > 0):
	    retries -= 1
	    l = self.get_length(gplayer)
	    if (l >= 0): break
	
	return l
		
    """
    " Returns the song length from a gstreamer player.
    """
    def get_length(self, gplayer):
	l = -1
	try:
	    l = gplayer.query_duration(gst.Format(gst.FORMAT_TIME), None)[0]
	    # Time is in nanoseconds.
	    l = float(l / 1000000000)
	except Exception,e:
	    logger.error("Error getting song length: %s" % str(e))
	
	return l

    """
    " Returns the current position from a gstreamer player.
    " Returns -1 if there was an error getting the current position.
    """
    def get_position(self, gplayer):
    	p = -1
	try:
	    p = gplayer.query_position(gst.Format(gst.FORMAT_TIME), None)[0]
	    # Time is in nanoseconds.
	    p = float(p / 1000000000)
	except:
	    p = -1

	return p
   
    """
    " Determines what the next song should be and returns
    " that song entry.
    """
    def choose_song(self, dir = PlayDirection.CURRENT):
        if (self.current is None):
            nextSong = self.first
	# If repeating, use same song.
	elif (self.repeat or dir == PlayDirection.CURRENT):
	    nextSong = self.current
	elif (dir == PlayDirection.FORWARD):
	    nextSong = self.current[2]
	    if (nextSong == None):
		nextSong = self.first
	elif (dir == PlayDirection.BACKWARD):
	    nextSong = self.current[0]
	    if (nextSong == None):
		nextSong = self.last

	return nextSong
   
    """
    " Sets our state and emits a state changed signal.
    """ 
    def set_state(self,newState):
        self.state = newState
        self.emit(Signals.STATE_CHANGED,newState)
    
    """
    " Next song in playlist
    """
    def next(self, stopCurrent = True):
	nextSong = self.choose_song(PlayDirection.FORWARD)
	self.play(nextSong[1].id, stopCurrent)
    
    """
    " Previous song in Playlist
    """
    def prev(self):
	nextSong = self.choose_song(PlayDirection.BACKWARD)
	self.play(nextSong[1].id)
    
    """
    " pauses playback
    """
    def pause(self):
	# Restore original suspend time when music is paused.
	self.config_set_suspend(0)

        try:
            if (self.state == State.PLAYING):
                self.players[self.curPlayer].set_state(gst.STATE_PAUSED)
                self.set_state(State.PAUSED)
        except:
            pass
    
    """
    " stops playback
    """
    def stop(self):
	# Restore original suspend time when music playing stops.
	self.config_set_suspend(0)

        try:
            if (self.state == State.PLAYING):
		self.players[self.curPlayer].set_state(gst.STATE_READY)
            self.set_state(State.STOPPED)
        except:
            pass

    """
    " Called to pause playback when the phone is activated.
    """
    def pause_for_phone(self):
        if (self.state == State.PLAYING):
	    logger.debug("Pausing playback at time %i due to phone call." 
		% self.songTimer)

	    try:
	    	self.players[self.curPlayer].set_state(gst.STATE_PAUSED)
            	self.set_state(State.PAUSED_PHONE)
	    except:
		logger.error("Failed to pause playback for phone call.")

    """
    " Called to resume playing when a phone call ends.
    """
    def resume_from_phone(self):
        if (self.state == State.PAUSED_PHONE):
	    logger.debug("Resuming playback at time %i." % self.songTimer)

	    try:
		self.players[self.curPlayer].set_state(gst.STATE_PLAYING)
            	self.set_state(State.PLAYING)
	    except:
		logger.error("Error resuming playback after phone call.")

    """
    " fills entry with track data
    """
    def fill_entry(self,array,entry):
        for val in array:
            m = re.match(" Artist\: (?P<value>.*)",val)
            if(m):
                entry.artist = m.group("value").strip()
            m = re.match(" Name\: (?P<value>.*)",val)                
            if(m):
                entry.title = m.group("value").strip()
            
    """
    " browses trough the filesystem
    """
    def browse(self,parentDir=None):
        if parentDir is None:
            parentDir = os.path.expanduser(self.cfg.get("gstreamer","musicdir","~"))
        ret = []        
        
        if parentDir != "/":
            ret.append(BrowserEntry(os.path.split(parentDir)[0],"..",True))
                        
        for file in os.listdir(parentDir):
            dir = False
            fullpath = os.path.join(parentDir,file)
            if os.path.isdir(fullpath):
                dir = True
            fullpath = unicode(fullpath,sys.getfilesystemencoding()).encode("utf-8")
            
            if self.filter(file,dir):
                ret.append(BrowserEntry(fullpath,file,dir))
        
        ret.sort(cmp=browserEntryCompare)
        self.emit(Signals.BROWSER_CHANGED,parentDir,ret)
    
    """
    " filters out private files and files with wrong endings.
    """
    def filter(self,file,dir):
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
    
    
    """
    " adds a browseEntry to the pl
    """
    def add(self,beId):
        
        fn = os.path.basename(beId)
        tpl = self.get_data(fn)
        entry = PlaylistEntry(beId,tpl[0],tpl[1],-1)
	entry.length = 0
        
        if self.first == None:
            self.first = [None,entry,None]
            #self.current = self.first
            self.last = self.first
        else:
            oldlast = self.last
            newlast = [oldlast,entry,None]
            oldlast[2] = newlast
            self.last = newlast
        
        self.entrydict[entry.id] = self.last
       
	# Get audio file information from mutagen.
	try:
	    ext   = os.path.splitext(beId)[1].lower()
	    audio = None

	    if   (ext == FILE_EXT_MP3):	 audio = MP3(beId, ID3=EasyID3)
	    elif (ext == FILE_EXT_OGG):  audio = OggVorbis(beId)
	    elif (ext == FILE_EXT_FLAC): audio = FLAC(beId)

	    if (audio != None):
		entry.artist = audio[TAG_NAME_ARTIST][0]
		entry.title  = audio[TAG_NAME_TITLE][0]
		entry.length = audio.info.length

	except Exception, e:
	    logger.warn("Invalid ID3 tag: %s" % e)

        self.emit_pl_changed()
        
    def emit_pl_changed(self):
        pl = []
        elem = self.first
        while elem is not None:
            pl.append(elem[1])
            elem = elem[2]
            
        self.emit(Signals.PL_CHANGED,pl)
        
    """
    " returns (artist,title) from regex filename match
    """
    def get_data(self,file):
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
    
    """
    " removes entry from pl
    """
    def remove(self,plid):
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
    
    """
    " seeks to pos in seconds
    """
    def seek(self,pos):
        if (self.state == State.PLAYING):
            self.songend = time.time() + (self.current[1].length - pos)
            #self.mplayer.command("seek",pos,2)
    
    """
    " shuts down backend
    """
    def shutdown(self):
	# Restore original suspend time on shutdown.
	self.config_set_suspend(0)

        try:
            PythmBackend.shutdown(self)
	    self.threadLoad.running = False
	    self.players[0].set_state(gst.STATE_NULL)
	    self.players[1].set_state(gst.STATE_NULL)
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
        self.entrydict = {}
        self.first = None
        self.current = None
        self.last = None
        self.emit_pl_changed()
    
    def add_dir(self,dir_to_add):
        """
        add a dir to pl
        """
	files = []
        for file in os.listdir(dir_to_add):
            dir = False
            fullpath = os.path.join(dir_to_add,file)
            if os.path.isdir(fullpath):
                dir = True
            if self.filter(file,dir):
                if dir:
                    self.add_dir(fullpath)
                else:
		    files.append(fullpath)
                    #self.add(fullpath)

	files.sort()
	for file in files:
	    self.add(file)
    
    """
    " gets called from StateChecker Thread.
    """
    def check_state(self, elapsedTime):
	# Only poll alsa for the current volume every so often
	# as is seems to take a non-insignficant load.	
	self.volTimer  += elapsedTime
	if (self.volTimer >= ALSA_POLL_TIME):
	  self.volTimer = 0  	
	  self.update_volume()
	
        try:
            if (self.state == State.PLAYING):

		self.songTimer += elapsedTime
		self.pollTimer += elapsedTime

		#print "Elapsed: " + str(elapsedTime) + " poll: " + str(self.pollTimer)

		# Only signal that time changed every so often to reduce
		# gui changes.
		if (self.pollTimer >= PLAYBACK_POLL_TIME):
		    # Attempt to sync up elapsed time with gstreamer.
		    p = self.get_position(self.players[self.curPlayer])
		    if (p > -1): self.songTimer = p

		    self.emit(Signals.POS_CHANGED, self.songTimer)

		    #print "Song time: " + str(self.songTimer)  + ", song length: " + str(self.songLength)
		    self.pollTimer = 0

		# Use the timer to determine if a song has ended 
		# and advance to the next. Do not stop the current song
		# just yet for a smooth cross fade.
		if (self.songTimer + elapsedTime + NEXT_SONG_FUDGE_TIME >= self.songLength):
                    self.next(False)

        except Exception,e:
            logger.error("Unexpected error in check_state: %s" % str(e))
                                                                                
    """
    " Populate sets default player settings at start time.
    " Should be called only after GUI init so that the
    " Signals emmitted by these calls have a place to go.
    """
    def populate(self):                                                         
        self.set_repeat(False)                                                  
        self.set_random(False)                                                  
        self.set_state(State.STOPPED)                                           
        self.emit_pl_changed()                                                  
        self.browse()                                                           
        # Init the alsa connection here since this sets the
	# GUI volume slider.                                                                        
	self.audio_init()

