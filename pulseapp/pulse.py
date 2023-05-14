# -*- coding: utf-8 -*-
#   VIM SETTINGS: {{{3
#   vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#   vim: set foldlevel=2 foldcolumn=2:
#   {{{2
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
from subprocess import Popen, PIPE, STDOUT
#   Notes:
#   {{{
#   2023-04-25T23:16:19AEST is two decimal places for qty really necessary?
#   2023-04-25T23:27:57AEST cascading if-s for poll_elapsed -> should they be elif-s?
#   }}}

#   old imports:
#   {{{
#from timeplot.decaycalc import DecayCalc
#from timeplot.timeplot import TimePlot
#from timeplot.plotdecayqtys import PlotDecayQtys
#from timeplot.util import TimePlotUtils
#   }}}

#path_debug_log = os.path.join(tempfile.gettempdir(), "pulseapp.debug.%s.txt" % str(int(time.time())))
#f_debug_log = open(path_debug_log, 'wt')

_logging_format="%(funcName)s: %(asctime)s %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"

logging.getLogger('matplotlib').setLevel(logging.WARNING)

log = logging.getLogger('pulse')
log.setLevel(logging.DEBUG)

#handler_stderr = logging.StreamHandler(sys.stderr)
#handler_stderr.setFormatter(logging.Formatter(_logging_format, datefmt=_logging_datetime))
#log.addHandler(handler_stderr)       #   comment to disable stderr output
#logging.basicConfig(stream=f_debug_log, format=_logging_format, datefmt=_logging_datetime)

logging.basicConfig(stream=sys.stderr, format=_logging_format, datefmt=_logging_datetime)

from .decaycalculator import DecayCalculator
from .utils import PulseAppUtils


class PulseApp(rumps.App):

    data = { 
        'delta_poll_qtys':          30,
        'poll_qty_precision':       1,
        'poll_qty_threshold':       0.01,
        'init_string':              "Hello There",
        'config_labels_file':       [ 'pulseapp.config', 'poll_items.txt' ],
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
        'gpgkey':                   "pantheon.redgrey@gpg.key",
        'datacopy_remove_duplicates': True,
        'data_cols':                { 'label': 0, 'qty': 1, 'datetime': 3, },
    }

    poll_items = { 
        'labels': [],
        'halflives': [],
        'onsets': [],
    }
    poll_qty = {
        'today': dict(),
        'now': dict(),
        'previous': dict(),
        'deltanow': dict(),
    }
    poll_elapsed = dict()

    def __init__(self):
        log.debug("__init__")
        #sys.stderr.write(f"path_debug_log=({path_debug_log})\n")

        self.enable_elapsed_notify = True

        super().__init__(self.data['init_string'], quit_button=None)

        #self.data['gpgkey'] = self.data['default_gpgkey']

        #   Setup menu items
        self.menu_item_qtytoday = rumps.MenuItem("qty:")
        self.menu_item_notifications = rumps.MenuItem("Notify On")
        self.menu_item_plottoday = rumps.MenuItem("Plot Today")
        self.menu_item_plotall = rumps.MenuItem("Plot All")
        self.menu_item_quit = rumps.MenuItem("Quit")

        self.menu.add(self.menu_item_qtytoday)
        self.menu.add(self.menu_item_notifications)
        self.menu.add(self.menu_item_plottoday)
        self.menu.add(self.menu_item_plotall)
        self.menu.add(self.menu_item_quit)

        self.error_str = ""

        #   Create path_dir_datacopy
        if not os.path.isdir(self.data['path_dir_datacopy']):
            log.warning("makedirs path_dir_datacopy=(%s)" % str(self.data['path_dir_datacopy']))
            os.makedirs(self.data['path_dir_datacopy'])

        #   Read resource files
        try:
            self._ReadResource_DataLabels()
        except Exception as e:
            log.error("Failed ReadResource, e=(%s)" % str(e))
            self.error_str = "!"
            exit(2)

        #   Initalize poll_qty
        for loop_label in self.poll_items['labels']:
            self.poll_qty['now'][loop_label] = 0
            self.poll_qty['today'][loop_label] = 0

        log.debug("self.data:\n%s\n" % pprint.pformat(self.data))
        self.timer_qtys = rumps.Timer(self.func_poll_qtys, self.data['delta_poll_qtys'])
        self.timer_qtys.start()


    def func_poll_qtys(self, sender):
        now = datetime.datetime.now()
        log.debug("now=(%s)" % str(now))

        #   Copy any new data from path_dir_datasource to path_dir_datacopy
        try:
            path_source = os.path.join(self.data['path_dir_datasource'], self.data['datasource_filename'])
            PulseAppUtils.CopyLogDataFile_DivideByMonth(path_source, self.data['path_dir_datacopy'], self.data['datacopy_prefix'], self.data['datacopy_postfix'], now, now, arg_overwrite=True, arg_includeMonthBefore=True, arg_gpg_key=self.data['gpgkey'], arg_remove_duplicate_lines=self.data['datacopy_remove_duplicates'])
        except Exception as e:
            log.error("CopyLogDataFile, e=(%s)" % str(e))
            self.error_str = "!"
            rumps.notification(f"pulseapp error", "CopyLogDataFile_DivideByMonth", "e=({e})")

        #   Get list of files to read data from
        try:
            located_filepaths = PulseAppUtils.GetFiles_FromMonthlyRange(self.data['path_dir_datacopy'], self.data['datacopy_prefix'], self.data['datacopy_postfix'], now, now, arg_includeMonthBefore=True)
        except Exception as e:
            log.error("GetAvailableFiles, e=(%s)" % str(e))
            self.error_str = "!"
            rumps.notification(f"pulseapp error", "GetAvailableFiles", "e=({e})")

        try:
            for loop_label, loop_halflife, loop_onset in zip(self.poll_items['labels'], self.poll_items['halflives'], self.poll_items['onsets']):
                log.debug("loop_label=(%s)" % str(loop_label))
                #   Read data from copied file(s) for loop_label
                try:
                    schedule_datetimes, schedule_qtys = PulseAppUtils.ReadTimestampedQtyScheduleData(located_filepaths, loop_label, self.data['data_cols'], self.data['data_delim'])
                except Exception as e:
                    log.error("ReadQtyScheduleData, e=(%s)" % str(e))
                    self.error_str = "!"
                    rumps.notification(f"pulseapp error", "ReadQtyScheduleData", "e=({e})")

                #   Calculate current qty for loop_label
                loop_qty_today = None
                try:
                    loop_qty_today = DecayCalculator.TotalQtyForDay(now, schedule_datetimes, schedule_qtys)
                except Exception as e:
                    log.error("TotalQtyForDay, e=(%s)" % str(e))
                    self.error_str = "!"
                    rumps.notification(f"pulseapp error", "TotalQtyForDay", "e=({e})")
                #   Calculate daily qty for loop_label
                loop_qty_now = None
                try:
                    loop_qty_now = DecayCalculator.CalculateQtyAtDT(now, schedule_datetimes, schedule_qtys, loop_halflife, loop_onset)
                except Exception as e:
                    log.error("CalculateQtyAtDT, e=(%s)" % str(e))
                    self.error_str = "!"
                    rumps.notification(f"pulseapp error", "CalculateQtyAtDT", "e=({e})")
                #   Round result to poll_qty_precision, and down to zero if less than poll_qty_threshold
                loop_qty_now = round(loop_qty_now, self.data['poll_qty_precision'])
                if (loop_qty_now < self.data['poll_qty_threshold']):
                    loop_qty_now = 0

                schedule_datetimes_last = max(schedule_datetimes)
                loop_deltanow = (now - schedule_datetimes_last).total_seconds()
                self.poll_qty['previous'][loop_label] = self.poll_qty['now'][loop_label]
                self.poll_qty['now'][loop_label] = loop_qty_now
                self.poll_qty['today'][loop_label] = loop_qty_today
                self.poll_qty['deltanow'][loop_label] = loop_deltanow

                log.debug(f"enable_elapsed_notify=({self.enable_elapsed_notify})")
                if self.enable_elapsed_notify and loop_label == "D-IR":
                    notifications_at = [ 45, 50, 55, 60, 65, 70, 75, 80, ]
                    for loop_m in notifications_at:
                        if self.poll_elapsed[loop_label] <= 1:
                            continue
                        if self.poll_elapsed[loop_label] >= loop_m * 60:
                            continue
                        if loop_deltanow < loop_m * 60:
                            continue
                        log.info(f"show notification, label=({loop_label}) just passed loop_m=({loop_m})")
                        #   rumps.notification(title, subtitle, message, data=None, sound=True)
                        rumps.notification(f"{loop_label} {loop_m}m", "", "")
                        log.info("notification DONE")
                        break

                self.poll_elapsed[loop_label] = loop_deltanow

                log.debug("loop_qty_today=(%s)" % str(loop_qty_today))
                log.debug("loop_qty_now=(%s)" % str(loop_qty_now))
                log.debug("loop_deltanow=(%s)" % str(loop_deltanow))

            log.debug(f"poll_elapsed=({self.poll_elapsed})")

            poll_title_str = self._CreatePollTitleStr()
            poll_todaysum_str = self._CreatePollTodaySumStr()

            sys.stderr.write("\n")

            self.title = poll_title_str
            self.menu_item_qtytoday.title = poll_todaysum_str
            log.debug("labels loop, DONE")
        except Exception as e:
            log.error("Labels loop, e=(%s)" % str(e))
            self.error_str = "!"
            rumps.notification(f"pulseapp error", "Labels loop", "e=({e})")

        #log.debug("Quit")
        #rumps.quit_application()

    def _CreatePollTitleStr(self):
        poll_str_qty = ""
        poll_str_delta = ""
        for loop_label in self.poll_items['labels']:
            loop_qty_now_previous = self.poll_qty['previous'][loop_label]
            loop_qty_now = self.poll_qty['now'][loop_label]
            loop_delta_now = self.poll_qty['deltanow'][loop_label]
            if loop_qty_now >= self.data['poll_qty_threshold']:
                poll_str_qty += str(loop_label[0]) + str(loop_qty_now)
                if (loop_qty_now > loop_qty_now_previous):
                    poll_str_qty += "🔺"
                else:
                    poll_str_qty += " "
                poll_str_delta += str(int(loop_delta_now/60)) + " "
        poll_title_str = poll_str_delta.strip() + "⏳" + poll_str_qty.strip()
        if self.enable_elapsed_notify:
            poll_title_str = "🔔 " + poll_title_str 
        else:
            poll_title_str = "🔕 " + poll_title_str
        log.debug("poll_title_str=(%s)" % str(poll_title_str))
        if self.error_str:
            return self.error_str
        return poll_title_str

    def _CreatePollTodaySumStr(self):
        poll_todaysum_str = "qty: "
        for loop_label in self.poll_items['labels']:
            loop_qty_today = self.poll_qty['today'][loop_label]
            poll_todaysum_str += loop_label[0] + "" + str(loop_qty_today) + " "

        poll_todaysum_str = poll_todaysum_str.strip()
        log.debug("poll_todaysum_str=(%s)" % str(poll_todaysum_str))
        return poll_todaysum_str


    @rumps.clicked('Notify On')
    def handle_toggle_notifications(self, _):
        """"""
        log.debug("toggle notifications called")
        new_label_str = ""
        if self.enable_elapsed_notify:
            new_label_str = "Notify Off"
            self.enable_elapsed_notify = False
        else:
            new_label_str = "Notify On"
            self.enable_elapsed_notify = True
        log.debug(f"new_label_str=({new_label_str})")
        self.menu_item_notifications.title = new_label_str
        poll_title_str = self._CreatePollTitleStr()
        self.title = poll_title_str

    @rumps.clicked('Quit')
    def handle_quit(self, _):
        """Handle Quit"""
        log.debug("Quit called")
        rumps.quit_application()

    def _ReadResource_DataLabels(self):
        """Read resource file config_labels_file to 'self.poll_items as tab-delimited values"""
        file_poll_items = importlib.resources.open_text(*self.data['config_labels_file'])
        log.debug("file_poll_items=(%s)" % str(file_poll_items))
        for loop_line in file_poll_items:
            loop_line = loop_line.strip()
            if loop_line[0] == '#':
                log.debug(f"skip commented line=({loop_line})")
                continue
            loop_line = loop_line.split("\t")
            if (len(loop_line) > 1):
                self.poll_items['labels'].append(loop_line[0])
                self.poll_items['halflives'].append(60 * int(loop_line[1]))
                self.poll_items['onsets'].append(60 * int(loop_line[2]))
                self.poll_elapsed[loop_line[0]] = 0
        if len(self.poll_items['labels']) == 0:
            log.error("failed to read any poll_items from file_poll_items=({file_poll_items})")
        file_poll_items.close()
        log.debug("data_labels=(%s)" % str(self.poll_items['labels']))
        log.debug("data_halflives=(%s)" % str(self.poll_items['halflives']))
        log.debug("data_onsets=(%s)" % str(self.poll_items['onsets']))

