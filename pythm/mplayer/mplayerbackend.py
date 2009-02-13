# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the pythm for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
""" TODO: Module description """

from pythm.backend import *
import os
import re
import sys
import alsaaudio
import ecore.evas
import time
from mplayer import MPlayer
from threading import Thread, Lock
from pythm.functions import *

# Time (seconds) to wait before polling alsa for the current volume.
ALSA_POLL_TIME = 3
# Name of the alsa mixer channel to contol.
ALSA_MIXER_NM = 'PCM'
# Time (seconds) between mplayer polls.
MLPAYER_POLL_TIME = 0.8

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
                pass


"""
" Backend for mplayer control
" Provides basic Player usage and file browsing.
"""
class MplayerBackend(PythmBackend):

    """
    " Constructor.
    """
    def __init__(self):
        self.mixer       = None
        self.lastVolume  = 0
        self.volTimer    = 0
        self.songTimer   = 0
        self.songLength  = 0
        self.pollTimer   = 0
        self.songChanged = False        # Flag for async song changed signal emmitt.

        PythmBackend.__init__(self,"mplayer")

    def startup(self,handler):
        try:
            self.lock = Lock()

            self.current = None
            self.first = None
            self.last = None
            self.entrydict = {}

            self.gotpos = False

            self.random = False
            self.repeat = False

            # Bind to mplayer.
            renice = self.cfg.get("mplayer","renice",None)
            self.mplayer = MPlayer(renice)
            endings = self.cfg.get("mplayer","endings","ogg,mp3")
            self.endings = endings.lower().split(",")

            self.filters  = self.cfg.get_array("mplayer","filters")

            # Init the connection to dbus for suspend time read/write.

            return PythmBackend.startup(self,handler)
        except Exception,e:
            logger.error("could not start mplayer %s " % str(e))
            return False

    def cbIdle( self, state):
        print "In the method"
        logger.error( "IDLE EVENT = %s" % state)

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
    " Plays a song from the playlist or starts playing of pleid=None
    " Does not perform a lock. Locks should be handled in invoking
    " methods.
    """
    def play(self, plid=None):
        # If paused, simply resume playing.
        if (self.state == State.PAUSED):
            self.mplayer.command("pause")
            self.set_state(State.PLAYING)

        # Check these states only State.PHONE_PAUSED
        # has special handling.
        elif (self.state == State.STOPPED or self.state == State.PLAYING):
            # Default state to stopped so main update loop will
            # stop drawing somg timer until after new song is
            # loaded.
            self.state = State.STOPPED
            #self.mplayer.command("pause")

            if (plid != None):
                self.choose_song(plid)

            if (self.current != None):
                entry   = self.current[1]
                fn      = entry.id
                #self.emit(Signals.SONG_CHANGED,entry)

                # DMR using arraycmd here takes mucho tiempo and
                # the song title information has already been
                # received from ID3 on playlist load.
                #array = self.mplayer.arraycmd("loadfile","======",fn)
                #self.fill_entry(array, entry)
                self.mplayer.command("loadfile", fn)
                entry.length = self.mplayer.cmd("get_time_length","ANS_LENGTH")

                """ DMR don't think we need this.
                retry = 0
                while (entry.length == -1 and retry < 5):
                    entry.length = self.mplayer.cmd("get_time_length","ANS_LENGTH")
                    if entry.length == -1:
                        time.sleep(0.25)
                    retry += 1
                """

                # DMR old way of doing things.
                #self.songstart = time.time
                #self.songend   = self.songstart + entry.length

                self.songTimer          = 0
                self.songLength = entry.length
                self.emit(Signals.SONG_CHANGED,entry)
                self.set_state(State.PLAYING)

    def choose_song(self,plid = None):
        if self.current is None:
            self.current = self.first

        if plid != None:
            self.current = self.entrydict[plid]

        if self.state == State.PLAYING:
            try:
                self.lock.acquire()
                self.play()
            except:
                logger.error("Unable to play chosen song.")

            self.lock.release()

    """
    " Next song in playlist
    """
    def next(self):
        if self.current == None:
            self.choose_song()
        else:
            if self.current[2] != None:
                self.choose_song(self.current[2][1].id)
            elif self.repeat:
                self.choose_song(self.first[1].id)

    """
    " Previous song in Playlist
    """
    def prev(self):
        if self.current != None:
            if self.current[0] != None:
                self.choose_song(self.current[0][1].id)
            elif self.repeat:
                self.choose_song(self.last[1].id)

    """
    " pauses playback
    """
    def pause(self):
        try:
            self.lock.acquire()
            if self.state == State.PLAYING:
                self.mplayer.command("pause")
                self.set_state(State.PAUSED)
        except:
            pass
        self.lock.release()

    """
    " stops playback
    """
    def stop(self):
        try:
            self.lock.acquire()
            if self.state == State.PLAYING:
                self.mplayer.command("stop")
            self.set_state(State.STOPPED)
        except:
            pass
        self.lock.release()

    """
    " Called to pause playback when the phone is activated.
    """
    def pause_for_phone(self):
        if (self.state == State.PLAYING):
            logger.debug("Pausing playback at time %i due to phone call."
                % self.songTimer)

            try:
                self.lock.acquire()

                # Use stop because the phone gets /dev/dsp lock.
                # See resume_from_call().
                self.mplayer.command("stop")
                self.set_state(State.PAUSED_PHONE)
            except:
                logger.error("Failed to pause playback for phone call.")

            self.lock.release()

    """
    " Called to resume playing when a phone call ends.
    """
    def resume_from_phone(self):
        if (self.state == State.PAUSED_PHONE):
            logger.debug("Resuming playback at time %i." % self.songTimer)

            try:
                self.lock.acquire()

                # Manually re-load the file into mplayer.
                # Need to do a loadfile since the phone will grab /dev/dsp
                # and we need to get it back.
                # Do not use self.play() to remove the overhead of
                # redrawing the UI for a new song.
                entry = self.current[1]
                self.mplayer.command("loadfile", entry.id)

                # Seek to where we last left off (done b/c of song reload).
                self.mplayer.command("seek", self.songTimer, 2)
                self.set_state(State.PLAYING)
            except:
                logger.error("Error resuming playback after phone call.")

            self.lock.release()

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
            parentDir = os.path.expanduser(self.cfg.get("mplayer","musicdir","~"))
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
        tpl = get_tags_from_file(fn)
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

        # Get audio file information from mutagen.
        read_audio_tags(entry, logger)

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
        if self.state == State.PLAYING:
            self.songend = time.time() + (self.current[1].length - pos)
            self.mplayer.command("seek",pos,2)

    """
    " shuts down backend
    """
    def shutdown(self):
        try:
            PythmBackend.shutdown(self)
            self.mplayer.quit()
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
                posValid = 1
                pos      = 0

                self.songTimer += elapsedTime
                self.pollTimer += elapsedTime

                #print "Elapsed: " + str(elapsedTime) + " poll: " + str(self.pollTimer)

                #length  = self.mplayer.cmd("get_time_length","ANS_LENGTH")
                #pos     = self.mplayer.cmd("get_time_pos",'ANS_TIME_POS')
                #percent = self.mplayer.cmd("get_percent_pos", "ANS_PERCENT_POSITION")

                # Only update by polling mplayer for the current
                # position every so often.
                if (self.pollTimer >= MLPAYER_POLL_TIME):
                    self.emit(Signals.POS_CHANGED, self.songTimer)
                    #print "Song time: " + str(self.songTimer)
                    self.pollTimer = 0

                    """
                    self.lock.acquire()
                    self.pollTimer = 0
                    pos = self.mplayer.cmd("get_time_pos",'ANS_TIME_POS')
                    self.lock.release()

                    #print "Pos: " + str(pos)

                    if (pos != None and is_numeric(pos)):
                        self.emit(Signals.POS_CHANGED, pos)
                    else:
                        posValid = 0
                    """
                # Use the timer to determine if a song has ended
                # and advance to the next.
                if (self.songTimer + 0.05 >= self.songLength or posValid == 0):
                    self.next()
        except:
            logger.error("Unexpected error in check_state: %s"
                         % sys.exc_info()[0])

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
