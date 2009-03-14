# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the pythm for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
""" Starts Pythm's GUI """

import os
import gtkgui
import backend
from config import PythmConfig, logger

def startPythm():
    """Start the Pythm and renice if it was requested
    """
    config = PythmConfig()
    try:
        renice_level = config.getint("pythm", "renice")
    except Exception, e:                # could be ValueError, TypeError
        renice_level = -5
        logger.warn("Assuming default renice=%d since failed to read "
                    "pythm.renice configuration: %s" % (renice_level, str(e)))
    if renice_level != 0:
        logger.debug("Renicing pythm to %d" % renice_level)
        try:
            os.nice(renice_level)
        except OSError, e:
            logger.error("Failed to renice: %s" % e)
    gtkgui.PythmGtk()

if __name__ == "__main__":
    startPythm()

