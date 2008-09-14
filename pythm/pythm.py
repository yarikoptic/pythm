import gtkgui
import backend
from config import PythmConfig

def startPythm():
    cfg = PythmConfig()
    cfgbackend = cfg.get("pythm","backend","mplayer")
    print "using " + cfgbackend + " backend"
    if cfgbackend == "mplayer":
        import mplayer
        backend = mplayer.MplayerBackend
    elif cfgbackend == "mpd":
        import mpd
        backend = mpd.MpdBackend
    else:
        backend = None
    
    if backend != None:
        gtkgui.PythmGtk(backend)
    else:
        print "no backend found"

if __name__ == "__main__":
    startPythm()
    
