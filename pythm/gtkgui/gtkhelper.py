import pygtk
pygtk.require('2.0')
import gtk

class ImageButton(gtk.Button):
    def __init__(self,stock):
        gtk.Button.__init__(self)
        img = gtk.image_new_from_stock(stock, gtk.ICON_SIZE_BUTTON)
        img.set_padding(3,15)
        self.set_image(img)