# -*- coding: utf-8 -*-
#   VIM SETTINGS: {{{3
#   vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#   vim: set foldlevel=2 foldcolumn=1:
#   }}}1
import sys
import os
import logging
import datetime
import importlib.resources
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
#   {{{2

#from timeplot.decaycalc import DecayCalc
#from timeplot.timeplot import TimePlot
#from timeplot.plotdecayqtys import PlotDecayQtys
#from timeplot.util import TimePlotUtils

from .decaycalculator import DecayCalculator
from .utils import PulseUtils

from subprocess import Popen, PIPE, STDOUT

_logging_format="%(funcName)s: %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"
logging.basicConfig(stream=sys.stderr, format=_logging_format, datefmt=_logging_datetime)

log = logging.getLogger('pulse')
logging.getLogger('matplotlib').setLevel(logging.WARNING)
log.setLevel(logging.DEBUG)

class PulseApp(rumps.App):

    data = { 
        'dt_poll_qtys':             10,
        'poll_qty_precision':       2,
        'poll_qty_threshold':       0.01,
        'init_string':              "Hello There",
        'config_labels_file':       [ 'config', 'poll_items.txt' ],
        'config_cols_file':         [ 'config', 'poll_columns.txt' ],
        'data_delim':               ",",
        'path_dir_sysout_cloud':    os.environ.get('mld_out_cloud_shared'),
        'path_dir_output_plot':     os.environ.get('mld_plots_pulse'),
        'path_dir_datasource':      os.environ.get('mld_icloud_workflowDocuments'),
        'path_dir_datacopy':        os.environ.get('mld_logs_pulse'),
        'path_dir_temp':            tempfile.mkdtemp(),
        'datasource_filename':      'Schedule.iphone.log',
        'datacopy_prefix':          'Schedule.calc.',
        'datacopy_postfix':         '.vimgpg',
        'default_gpgkey':           "pantheon.redgrey@gpg.key",
        'datacopy_remove_duplicates': True,
    }

    data_cols = dict()
    poll_items = { 
        'labels': [],
        'halflives': [],
        'onsets': [],
    }
    poll_qty = {
        'today': dict(),
        'now': dict(),
        'previous': dict(),
    }

    def __init__(self):

        log.debug("__init__")
        super().__init__(self.data['init_string'], quit_button=None)

        self.data['gpgkey'] = self.data['default_gpgkey']

        #   Setup menu items
        self.menu_item_qtytoday = rumps.MenuItem("qty:")
        self.menu_item_quit = rumps.MenuItem("Quit")
        self.menu.add(self.menu_item_qtytoday)
        self.menu.add(self.menu_item_quit)

        #   Create path_dir_datacopy
        if not os.path.isdir(self.data['path_dir_datacopy']):
            log.warning("makedirs _datacopy_dir=(%s)" % str(self.data['path_dir_datacopy']))
            os.makedirs(self.data['path_dir_datacopy'])

        #   Read resource files
        try:
            self._ReadResource_DataCols()
            self._ReadResource_DataLabels()
        except Exception as e:
            log.error("Failed ReadResource, e=(%s)" % str(e))
            exit(2)

        #   Initalize poll_qty
        for loop_label in self.poll_items['labels']:
            self.poll_qty['now'][loop_label] = 0
            self.poll_qty['today'][loop_label] = 0

        self.timer_qtys = rumps.Timer(self.func_poll_qtys, self.data['dt_poll_qtys'])
        self.timer_qtys.start()


    def func_poll_qtys(self, sender):
        now = datetime.datetime.now()
        log.debug("now=(%s)" % str(now))

        #   Copy any new data from path_dir_datasource to path_dir_datacopy
        try:
            path_source = os.path.join(self.data['path_dir_datasource'], self.data['datasource_filename'])
            PulseUtils.CopyLogDataFile_DivideByMonth(path_source, self.data['path_dir_datacopy'], self.data['datacopy_prefix'], self.data['datacopy_postfix'], now, now, overwrite=True, includeMonthBefore=True, gpgkey=self.data['gpgkey'], remove_duplicates=self.data['datacopy_remove_duplicates'])
        except Exception as e:
            log.error("CopyLogDataFile, e=(%s)" % str(e))

        #   Get list of files to read data from
        try:
            located_filepaths = PulseUtils.GetAvailableFiles_FromMonthlyRange(self.data['path_dir_datacopy'], self.data['datacopy_prefix'], self.data['datacopy_postfix'], now, now, includeMonthBefore=True)
        except Exception as e:
            log.error("GetAvailableFiles, e=(%s)" % str(e))

        for loop_label, loop_halflife, loop_onset in zip(self.poll_items['labels'], self.poll_items['halflives'], self.poll_items['onsets']):
            #   Read data from copied file(s) for loop_label
            try:
                data_dt, data_qty = PulseUtils.ReadQtyScheduleData(located_filepaths, loop_label)
            except Exception as e:
                log.error("ReadQtyScheduleData, e=(%s)" % str(e))

            #   Calculate current qty for loop_label
            try:
                loop_qty_today = DecayCalculator.TotalQtyForDay(now, data_dt, data_qty)
            except Exception as e:
                log.error("TotalQtyForDay, e=(%s)" % str(e))

            #   Calculate daily qty for loop_label
            try:
                loop_qty_now = DecayCalculator.CalculateQtyAtDT(now, data_dt, data_qty, loop_halflife, loop_onset)
            except Exception as e:
                log.error("CalculateQtyAtDT, e=(%s)" % str(e))

            #   Round result to poll_qty_precision, and down to zero if less than poll_qty_threshold
            loop_qty_now = round(loop_qty_now, self.data['poll_qty_precision'])
            if (loop_qty_now < self.data['poll_qty_threshold']):
                loop_qty_now = 0

            log.debug("loop_qty_today=(%s)" % str(loop_qty_today))
            log.debug("loop_qty_now=(%s)" % str(loop_qty_now))
 

        log.debug("Quit")
        rumps.quit_application()

    @rumps.clicked('Quit')
    def handle_quit(self, _):
        """Handle Quit"""
        #   {{{
        log.debug("Quit called")
        rumps.quit_application()
        #   }}}

    def _ReadResource_DataCols(self):
        """Read resource file config_cols_file to 'self.data_cols' as tab-delimited integers. Values (in order): [ label, qty, datetime ]"""
        #   {{{
        file_data_cols = importlib.resources.open_text(*self.data['config_cols_file'])
        log.debug("file_data_cols=(%s)" % str(file_data_cols))
        filedata = file_data_cols.read().strip()
        _data_cols_str = filedata.split("\t")
        self.data_cols['label'] = int(_data_cols_str[0])
        self.data_cols['qty'] = int(_data_cols_str[1])
        self.data_cols['datetime'] = int(_data_cols_str[2])
        file_data_cols.close()
        log.debug("data_cols=(%s)" % str(self.data_cols))
        #   }}}

    def _ReadResource_DataLabels(self):
        """Read resource file config_labels_file to 'self.poll_items as tab-delimited values"""
        #   {{{
        file_poll_items = importlib.resources.open_text(*self.data['config_labels_file'])
        log.debug("file_poll_items=(%s)" % str(file_poll_items))
        for loop_line in file_poll_items:
            loop_line = loop_line.strip().split("\t")
            if (len(loop_line) > 1):
                self.poll_items['labels'].append(loop_line[0])
                self.poll_items['halflives'].append(60 * int(loop_line[1]))
                self.poll_items['onsets'].append(60 * int(loop_line[2]))
        file_poll_items.close()
        log.debug("data_labels=(%s)" % str(self.poll_items['labels']))
        log.debug("data_halflives=(%s)" % str(self.poll_items['halflives']))
        log.debug("data_onsets=(%s)" % str(self.poll_items['onsets']))
        #   }}}



