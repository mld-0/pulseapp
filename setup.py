#   VIM SETTINGS: {{{3
#   vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#   vim: set foldlevel=2 foldcolumn=1:
#   }}}1
from setuptools import setup, find_packages
import pkg_resources
import re
#import pulseapp

exec(open('pulseapp/version.py').read())
print("got version=(%s)" % __version__)

APP = [ 'main.py' ]
dependencies = [ 'rumps', 'pandas', 'dateparser' ]
#install_packages = find_packages(include=['pulseapp', 'config', ])
install_packages = find_packages(include=['pulseapp'])

#DATA_FILES = []
#PY2APP_OPTIONS = {
#    'argv_emulation': True,
#    'iconfile': 'icon-pulse.icns',
#    'plist': {
#        'CFBundleShortVersionString': __version__,
#        'LSUIElement': True,
#    },
#    #   Ongoing: 2022-06-08T23:06:45AEST 'package_dir' not tested with py2app (py2app has not been working in any case)
#    'package_dir': package_dir,
#    'packages': packages,
#    'includes': packages,
#}

setup( 
    name="pulseapp",
    version=__version__,
    app=APP,

    packages = install_packages,
    install_requires = dependencies,
    tests_require = [ 'unittest', ],

    #data_files=DATA_FILES,
    #options={'py2app': PY2APP_OPTIONS},
    #package_dir = package_dir,
)

