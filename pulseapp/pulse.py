# -*- coding: utf-8 -*-
#   VIM SETTINGS: {{{3
#   vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#   vim: set foldlevel=2 foldcolumn=1:
#   }}}1
import sys
import os
import logging
import datetime
import importlib
import time
import math
import rumps
import csv
import inspect
import weakref
import pkgutil
import webbrowser
import tempfile
import dateutil
import subprocess
import pprint
import pandas

#from timeplot.decaycalc import DecayCalc
#from timeplot.timeplot import TimePlot
#from timeplot.plotdecayqtys import PlotDecayQtys
#from timeplot.util import TimePlotUtils

from subprocess import Popen, PIPE, STDOUT

_logging_format="%(funcName)s: %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"
logging.basicConfig(stream=sys.stderr, format=_logging_format, datefmt=_logging_datetime)

log = logging.getLogger('pulse')
logging.getLogger('matplotlib').setLevel(logging.WARNING)
log.setLevel(logging.DEBUG)

class PulseApp(rumps.App):
    
    def __init__(self):
        log.debug("__init__")


