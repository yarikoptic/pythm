# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the pythm for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Distutils setup for pythm installation"""

from distutils.core import setup
import glob

setup(name='Pythm',
        version='0.5.1',
        description='Frontend for mplayer and mpd',
        author='Matthias Hans',
        author_email='ughl0r@yahoo.de',
        url='http://pythm.projects.openmoko.org',
        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Gnome',
            'Intended Audience :: End Users/Phone UI',
            'License :: GNU General Public License (GPL)',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Multimedia :: Sound :: Players',
            ],
        package_dir= {'pythm':'pythm'},
        packages=['pythm', 'pythm.gtkgui', 'pythm.backend',
                  'pythm.mplayer', 'pythm.mpd', 'pythm.gstreamer'],
        data_files=[('share/applications', ['data/pythm.desktop']),
                    ('/etc', ['conf/pythm.conf']),
                    ('share/pythm/', ['doc/README']),
                    ('share/icons', ['data/pythm.png'])
                    ],
        scripts = ['bin/pythm']
     )
