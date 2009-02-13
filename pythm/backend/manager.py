# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the pythm for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
""" TODO: Module description """


from pythm.config import PythmConfig

class BackendManager():

    def __init__(self):
        self.cfg = PythmConfig()

    def get_backends(self):
        return self.cfg.get_backends()


    def disconnect(self,backend):
        if backend != None and backend.is_connected():
            backend.disconnect()

    def connect(self,backend):
        self.disconnect(self.cfg.get_backend())
        if not backend.is_connected():
            backend.reconnect()
            self.cfg.set_active_backend(backend)
            backend.populate()

    def start(self,backend,callback):
        self.disconnect(self.cfg.get_backend())
        return backend.startup(callback)

    def stop(self,backend):
        if backend.is_started():
            backend.shutdown()
