# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the pythm for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
""" TODO: Module description """

import pygtk
pygtk.require('2.0')
import gtk


from pagelist import *
from pageplay import *
from pagebrowse import *
from pagebackend import *
from pythm.lang import _
from pythm.backend import ThreadedBackend
from pythm.config import PythmConfig

class PythmGtk:

    def hello(self, widget, data=None):
        print "Hello World"

    def delete_event(self, widget, event, data=None):
        print "delete event occurred"
        # Change FALSE to TRUE and the main window will not be destroyed
        return False

    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        for backend in self.cfg.get_backends():
            backend.shutdown()
        gtk.main_quit()

    def __init__(self):
        # create a new window
        gtk.gdk.threads_init()
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.resize(480,640)
        self.window.set_title(_("pythm"))

        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)

        self.cfg = PythmConfig()

        self.vbox = gtk.VBox()
        self.tabs = gtk.Notebook()
        self.tabs.set_property("homogeneous",True)
        play = PagePlay()
        img = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_LARGE_TOOLBAR)
        img.set_padding(3,3)
        self.tabs.append_page(play,img)
        self.tabs.child_set(play,"tab-expand",True)
        img = gtk.image_new_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_LARGE_TOOLBAR)
        img.set_padding(3,3)
        self.tabs.append_page(PageList(),img)
        img = gtk.image_new_from_stock(gtk.STOCK_FIND, gtk.ICON_SIZE_LARGE_TOOLBAR)
        img.set_padding(3,3)
        self.tabs.append_page(PageBrowse(),img)

        img = gtk.image_new_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_LARGE_TOOLBAR)
        img.set_padding(3,3)
        box = gtk.HBox()
        self.tabs.append_page(PageBackend(),img)

        self.vbox.add(self.tabs)


        # This packs the button into the window (a GTK container).
        self.window.add(self.vbox)

        # and the window
        self.window.show_all()

        gtk.main()
