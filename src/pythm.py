import pygtk
pygtk.require('2.0')
import gtk
import gobject
import gtkgui
import backend
import mplayer.mplayerbackend

def gtkcallback(func,*args):
    """
    callback method for signals of backend (out of gtk-thread)
    """
    gobject.idle_add(func,*args)

def startPythm():
    gtk.gdk.threads_init()
    backend = mplayer.MplayerBackend(gtkcallback)
    gui = gtkgui.PythmGtk(backend)
    gtk.main()

    

if __name__ == "__main__":
    startPythm()
    
    
# helper funcs

def is_numeric(val):
    try:
        val + 1
        return True
    except Exception,e:
        return False