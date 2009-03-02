import gst
import pygst

class GPlayer:
    """
    Class to contain all the junk we need to play various formats in gstreamer.
    """
    
    def __init__(self):
        """
        Constructor.
        """
        
        self.player = None
        self.source = None
        self.conv = None
        self.sink = None
        self.volume = None
        self.decoders = []          # One decoder for each media type.
        self.demuxers = []          # One muxer for each media type.
        
        self.eMedia = MediaTypes.NONE           # Current media type the player is prepared to play.
        self.timeFmt = gst.Format(gst.FORMAT_TIME)
        
    def init(self):
        """
        Initialize all the gstreamer pipeline pieces for all media types.
        """
        
        # MP3
        self.decoders.append(gst.element_factory_make("mad", "decode-mp3"))
        self.demuxers.append(None);
        
        # OGG
        self.decoders.append(gst.element_factory_make("ivorbisdec", "decode-ogg"))
        self.demuxers.append(gst.element_factory_make("oggdemux", "demux-vorbis"));
        self.demuxers[MediaTypes.OGG].connect("pad-added", self.ogg_demux_cb)

        """
        # FLAC
        #DMR TODO Add flac support.
        self.decoders.append(None)
        self.demuxers.append(None);
        """
        
        self.source = gst.element_factory_make("filesrc", "src-file")
        self.conv = gst.element_factory_make("audioconvert", "converter")
        self.sink = gst.element_factory_make("alsasink", "output")
        self.volume = gst.element_factory_make("volume", "volume")
        
        self.player = gst.Pipeline("player")
        
        self.set_media(MediaTypes.MP3)
        
        #self.player.set_property('video-sink', None)
         
    def set_media(self, eMedia):
        """
        Prepares the player to play the given type of media.
        Removes the current pipeline and replaces it with a new one if the media type is different
        than the current media type.
        \param eMedia Media type to play. One of MediaTypes.
        """

        if (eMedia != MediaTypes.MP3 and eMedia != MediaTypes.OGG):
            return False
       
        # No change needed.
        if (self.eMedia == eMedia): return True
            
        # First remove the current pipeline.
        # Do not do this the first time through.
        if (self.eMedia != MediaTypes.NONE):
            self.player.remove(self.source)
            self.player.remove(self.conv)
            self.player.remove(self.sink)
            self.player.remove(self.volume)
        
        if (self.player.get_by_name("decode-ogg") is not None):
            self.player.remove(self.decoders[MediaTypes.OGG])
            self.player.remove(self.demuxers[MediaTypes.OGG])
        elif (self.player.get_by_name("decode-mp3") is not None):
            self.player.remove(self.decoders[MediaTypes.MP3])
        """
        elif (self.player.get_by_name("decode-flac") is not None):
            #DMR TODO Add flac support.
            pass
        """

        # Next, build the corrert pipeline.
        if (eMedia == MediaTypes.MP3):
            self.player.add(self.source, self.decoders[MediaTypes.MP3], self.conv, 
                self.volume, self.sink)
            gst.element_link_many(self.source, self.decoders[MediaTypes.MP3], 
                self.conv,self.volume, self.sink)
        elif (eMedia == MediaTypes.OGG):
            self.player.add(self.source, self.demuxers[MediaTypes.OGG], 
                self.decoders[MediaTypes.OGG], self.conv, self.volume, self.sink)
            gst.element_link_many(self.source, self.demuxers[MediaTypes.OGG])
            gst.element_link_many(self.decoders[MediaTypes.OGG], self.conv, 
                self.volume, self.sink)
        """
        elif (eMedia == MediaTypes.FLAC):
            #DMR TODO Add flac support.
            pass
        """

        self.eMedia = eMedia
        return True

    def ogg_demux_cb(self, demuxer, pad):
        adec_pad = self.decoders[MediaTypes.OGG].get_pad("sink")
        pad.link(adec_pad)
            
    def get_bus(self):
        """
        Returns the gstreamer bus attached to the player.
        """
        return self.player.get_bus();
        
    def get_duration(self):
        """ 
        Returns the length (float, seconds) of the current track.
        Only works if the player state has been set to Playing.
        """
        return float(self.player.query_duration(self.timeFmt, None)[0] / 1000000000)
    
    def get_position(self):
        """
        Returns the current position (float, seconds) of the current track.
        Only works if the player state has been set to Playing.
        """
        return float(self.player.query_position(self.timeFmt, None)[0] / 1000000000)
            
    def set_file(self, fn):
        """
        Sets the file name the player is to play.
        \param fn Path to file to load.
        """
        self.player.get_by_name("src-file").set_property("location", fn)
            
    def set_state(self, eState):
        """ 
        Sets the state in the gstreamer player the given state.
        \param eState New state.
        """
        self.player.set_state(eState)

    def set_volume(self, iVol):
        """
        Set the playback volume of the player.
        \param iVol Volume level from 0 to 100
        """
        self.volume.set_property("volume", float(iVol)/100)
        
    def seek(self, iSeconds):
        """
        Seeks the player to the given time in seconds.
        """
        self.player.seek_simple(self.timeFmt, gst.SEEK_FLAG_FLUSH, iSeconds * 10000000)
        
class MediaTypes:
    """
    Supperted media types for the GPlayer class.
    """
    NONE = -1
    MP3 = 0
    OGG = 1
    #FLAC = 2
    COUNT = 2