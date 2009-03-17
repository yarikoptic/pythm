# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#

#
# Config file section names:
#
CFG_SECTION_PYTHM = "pythm"     # pythm section: general settings.
CFG_SECTION_BROWSER = "browser" # browser section: GUI browser.

#
# Config file setting names:
#
CFG_SETTING_NOSUSPEND = "no_suspend" # No suspend during playback.
CFG_SETTING_SUSPENDIFACE = "suspend_iface" # No suspend dbus interface.
CFG_SETTING_MUSICDIR = "musicdir" # Default music directory.
CFG_SETTING_FILEENDINGS = "endings" # Viable file name endings.
CFG_SETTING_FILEFILTERS = "filters" # File name filters.

# Suspend interface settings possible values:
SUSPEND_IFACE_FSO = "fso" # for frameworkd.
SUSPEND_IFACE_E = "e"     # for enlightenment.
