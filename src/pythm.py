import pygtk
pygtk.require('2.0')
import gtk
import gtkgui
import backend
import mplayer.mplayerbackend

if __name__ == "__main__":
    backend = mplayer.MplayerBackend()
    gui = gtkgui.PythmGtk(backend)
    gtk.main()