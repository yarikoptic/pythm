from distutils.core import setup
import glob
    
setup(name='Pythm',
        version='0.4',
        description='Frontend for mplayer and mpd',
        author='Matthias Hans',
        author_email='ughl0r@yahoo.de',
        url='http://pythm.projects.openmoko.org',
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'Environment :: Gnome',
            'Intended Audience :: End Users/Phone UI',
            'License :: GNU General Public License (GPL)',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Multimedia :: Sound :: Players',
            ],
        package_dir= {'pythm':'pythm'},
        packages=['pythm','pythm.gtkgui','pythm.backend','pythm.mplayer','pythm.mpd'],
        data_files=[('share/applications', ['data/pythm.desktop'])],
        scripts = ['pythm-bin']
     )
