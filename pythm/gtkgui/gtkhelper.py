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
        img = gtk.image_new_from_stock(stock, gtk.ICON_SIZE_BUTTON)
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
