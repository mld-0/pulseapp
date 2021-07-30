#   VIM SETTINGS: {{{3
#   vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#   vim: set foldlevel=2 foldcolumn=1:
#   }}}1
import sys
import os
import logging
import unittest
import importlib.resources
import tempfile
import datetime
import time
import pprint
from pulseapp.pulse import PulseApp
from pulseapp.utils import PulseAppUtils
from pulseapp.decaycalculator import DecayCalculator

_logging_format="%(funcName)s: %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"
logging.basicConfig(stream=sys.stderr, format=_logging_format, datefmt=_logging_datetime)

log = logging.getLogger('pulse')
log.setLevel(logging.DEBUG)

with importlib.resources.path("pulseapp.tests.data", "encrypted-example.gpg") as p:
    path_test_encrypted_example_gpg = str(p)

path_test_schedule = os.path.join(os.environ.get('mld_icloud_workflowDocuments'), 'Schedule.iphone.log')

#_testdir = tempfile.TemporaryDirectory()
#path_testdir = os.path.realpath(_testdir.name)
path_testdir = "/tmp/pulseutils.test.temp"
if not os.path.isdir(path_testdir):
    os.mkdir(path_testdir)

class Test_DecayCalculator(unittest.TestCase):

    data = PulseApp.data

    #   Ongoing: 2021-07-30T14:58:13AEST dedicated test data -> predicable (assertable) results

    def test_CalculateQtyAtDT(self):
        self.assertEqual(os.path.isfile(path_test_schedule), True)
        now = datetime.datetime.now()
        path_source = os.path.join(self.data['path_dir_datasource'], self.data['datasource_filename'])
        PulseAppUtils.CopyLogDataFile_DivideByMonth(path_source, path_testdir, self.data['datacopy_prefix'], self.data['datacopy_postfix'], now, now, arg_overwrite=True, arg_includeMonthBefore=True, arg_gpg_key=self.data['gpgkey'], arg_remove_duplicate_lines=self.data['datacopy_remove_duplicates'])

        schedule_files = PulseAppUtils.GetFiles_FromMonthlyRange(path_testdir, self.data['datacopy_prefix'], self.data['datacopy_postfix'], now, now, True)

        schedule_datetimes, schedule_qtys = PulseAppUtils.ReadTimestampedQtyScheduleData(schedule_files, "D-IR", self.data['data_cols'], self.data['data_delim'])
        result_DIR_qty_now = DecayCalculator.CalculateQtyAtDT(now, schedule_datetimes, schedule_qtys, 45*60, 20*60)
        print("result_DIR_qty_now=(%s)" % str(result_DIR_qty_now))

        schedule_datetimes, schedule_qtys = PulseAppUtils.ReadTimestampedQtyScheduleData(schedule_files, "Can-S", self.data['data_cols'], self.data['data_delim'])
        result_Can_qty_now = DecayCalculator.CalculateQtyAtDT(now, schedule_datetimes, schedule_qtys, 40*60, 3*60)
        print("result_Can_qty_now=(%s)" % str(result_Can_qty_now))

    def test_TotalQtyForDay(self):
        self.assertEqual(os.path.isfile(path_test_schedule), True)
        now = datetime.datetime.now()
        path_source = os.path.join(self.data['path_dir_datasource'], self.data['datasource_filename'])
        PulseAppUtils.CopyLogDataFile_DivideByMonth(path_source, path_testdir, self.data['datacopy_prefix'], self.data['datacopy_postfix'], now, now, arg_overwrite=True, arg_includeMonthBefore=True, arg_gpg_key=self.data['gpgkey'], arg_remove_duplicate_lines=self.data['datacopy_remove_duplicates'])

        schedule_files = PulseAppUtils.GetFiles_FromMonthlyRange(path_testdir, self.data['datacopy_prefix'], self.data['datacopy_postfix'], now, now, True)

        schedule_datetimes, schedule_qtys = PulseAppUtils.ReadTimestampedQtyScheduleData(schedule_files, "D-IR", self.data['data_cols'], self.data['data_delim'])
        result_DIR_qty_today = DecayCalculator.TotalQtyForDay(now, schedule_datetimes, schedule_qtys)
        print("result_DIR_qty_today=(%s)" % str(result_DIR_qty_today))

        schedule_datetimes, schedule_qtys = PulseAppUtils.ReadTimestampedQtyScheduleData(schedule_files, "Can-S", self.data['data_cols'], self.data['data_delim'])
        result_Can_qty_today = DecayCalculator.TotalQtyForDay(now, schedule_datetimes, schedule_qtys)
        print("result_Can_qty_today=(%s)" % str(result_Can_qty_today))


if __name__ == "__main__":
    unittest.main()

