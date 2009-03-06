# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the pythm for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
""" TODO: Module description """

import gettext
import logging

logger = logging.getLogger("pythm")

def dummy(str):
    return str

once = False

if not once:
    try:
        t = gettext.translation('pythm', 'locale')
        _ = t.lgettext
        once = True
    except Exception,e:
        logger.warning("No Locale found, falling back! Error was: %s" % e)
        _ = dummy
        once = True


