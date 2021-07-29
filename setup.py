#   VIM SETTINGS: {{{3
#   vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#   vim: set foldlevel=2 foldcolumn=1:
#   }}}1
from setuptools import setup
import pkg_resources
import re
import pulseapp

version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('pulseapp/__main__.py').read(),
    re.M
    ).group(1)

APP = [ 'main.py' ]
packages = [ 'rumps', 'pulseapp', 'pandas', 'dateparser' ]

DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icon-pulse.icns',
    'plist': {
        'CFBundleShortVersionString': version,
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
    install_requires=packages
)

