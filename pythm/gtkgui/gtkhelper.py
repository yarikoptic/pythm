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

use_sc=True
try:
    import mokoui
    use_sc=False
except:
    pass

class ImageButton(gtk.Button):
    def __init__(self,stock):
        gtk.Button.__init__(self)
        img = gtk.image_new_from_stock(stock, gtk.ICON_SIZE_LARGE_TOOLBAR)
        img.set_padding(3,15)
        self.set_image(img)


def get_scrolled_widget():
    if use_sc:
        sc = gtk.ScrolledWindow()
        sc.set_property("vscrollbar-policy",gtk.POLICY_AUTOMATIC)
        sc.set_property("hscrollbar-policy",gtk.POLICY_AUTOMATIC)
        return sc
    else:
        return mokoui.FingerScroll()
