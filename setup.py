#   VIM SETTINGS: {{{3
#   vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#   vim: set foldlevel=2 foldcolumn=1:
#   }}}1
from setuptools import setup
import pkg_resources
import re
import pulseapp

exec(open('pulseapp/version.py').read())

APP = [ 'main.py' ]
packages = [ 'rumps', 'pulseapp', 'pandas', 'dateparser' ]

DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icon-pulse.icns',
    'plist': {
        'CFBundleShortVersionString': __version__,
        'LSUIElement': True,
    },
    'packages': packages,
    'includes': packages,
}

setup( 
    app=APP,
    name="PulseApp",
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=packages,
    install_requires=packages,
    version=__version__,
)

