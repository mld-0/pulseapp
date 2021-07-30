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

_logging_format="%(funcName)s: %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"
logging.basicConfig(stream=sys.stderr, format=_logging_format, datefmt=_logging_datetime)

log = logging.getLogger('pulse')
log.setLevel(logging.DEBUG)


gpg_key_test = "pantheon.redgrey@gpg.key"

with importlib.resources.path("pulseapp.tests.data", "encrypted-example.gpg") as p:
    path_test_encrypted_example_gpg = str(p)

path_test_schedule = os.path.join(os.environ.get('mld_icloud_workflowDocuments'), 'Schedule.iphone.log')

#_testdir = tempfile.TemporaryDirectory()
#path_testdir = os.path.realpath(_testdir.name)
path_testdir = "/tmp/pulseutils.test.temp"
if not os.path.isdir(path_testdir):
    os.mkdir(path_testdir)

class Test_PulseAppUtils(unittest.TestCase):

    data = PulseApp.data

    def test_ReadTimestampedQtyScheduleData(self):
        self.assertEqual(os.path.isfile(path_test_schedule), True)
        now = datetime.datetime.now()
        path_source = os.path.join(self.data['path_dir_datasource'], self.data['datasource_filename'])
        PulseAppUtils.CopyLogDataFile_DivideByMonth(path_source, path_testdir, self.data['datacopy_prefix'], self.data['datacopy_postfix'], now, now, arg_overwrite=True, arg_includeMonthBefore=True, arg_gpg_key=self.data['gpgkey'], arg_remove_duplicate_lines=self.data['datacopy_remove_duplicates'])
        result_files = PulseAppUtils.GetFiles_FromMonthlyRange(path_testdir, self.data['datacopy_prefix'], self.data['datacopy_postfix'], now, now, True)
        result_datetimes, result_qtys = PulseAppUtils.ReadTimestampedQtyScheduleData(result_files, "D-IR", self.data['data_cols'], self.data['data_delim'])
        result_datetimes, result_qtys = PulseAppUtils.ReadTimestampedQtyScheduleData(result_files, "Can-S", self.data['data_cols'], self.data['data_delim'])
        #   Continue: 2021-07-30T14:18:52AEST verify results of ReadTimestampedQtyScheduleData() -> use of dedicated test file <- predictable results which can be used with assert?


    def test_CopyLogDataFile_DivideByMonth(self):
        self.assertEqual(os.path.isfile(path_test_schedule), True)
        now = datetime.datetime.now()
        #   Copy any new data from path_dir_datasource to path_dir_datacopy
        path_source = os.path.join(self.data['path_dir_datasource'], self.data['datasource_filename'])
        PulseAppUtils.CopyLogDataFile_DivideByMonth(path_source, path_testdir, self.data['datacopy_prefix'], self.data['datacopy_postfix'], now, now, arg_overwrite=True, arg_includeMonthBefore=True, arg_gpg_key=self.data['gpgkey'], arg_remove_duplicate_lines=self.data['datacopy_remove_duplicates'])
        #   Ongoing: 2021-07-30T11:49:02AEST Get sha256 of resulting file(s), call CopyLogDataFile_DivideByMonth() again, and verify files aren't changed given no new data
        #   Ongoing: 2021-07-30T11:49:46AEST Use a file that isn't (the real icloud schedule document) for testing
        #   Continue: 2021-07-29T23:31:58AEST pulseapp, test_pulseutils, verify contents of path_testdir
        #   Continue: 2021-07-29T23:32:14AEST pulseapp, test_pulseutils, CopyLogDataFile_DivideByMonth, do not update file if sha256 of contents match


    def test_GetAvailableFiles_FromMonthlyRange(self):
        self.assertEqual(os.path.isfile(path_test_schedule), True)
        now = datetime.datetime.now()
        #   Copy any new data from path_dir_datasource to path_dir_datacopy
        path_source = os.path.join(self.data['path_dir_datasource'], self.data['datasource_filename'])
        PulseAppUtils.CopyLogDataFile_DivideByMonth(path_source, path_testdir, self.data['datacopy_prefix'], self.data['datacopy_postfix'], now, now, arg_overwrite=True, arg_includeMonthBefore=True, arg_gpg_key=self.data['gpgkey'], arg_remove_duplicate_lines=self.data['datacopy_remove_duplicates'])
        result_files = PulseAppUtils.GetFiles_FromMonthlyRange(path_testdir, self.data['datacopy_prefix'], self.data['datacopy_postfix'], now, now, True)
        self.assertEqual(len(result_files), 2, "Should be two files, current month and previous month")
        for loop_file in result_files:
            self.assertEqual(os.path.isfile(loop_file), True)


    def test_gpg_decryptfile2string(self):
        result_text = PulseAppUtils.GPG_DecryptFile2String(path_test_encrypted_example_gpg)
        self.assertEqual(result_text, "abc\n")

    def test_gpg_encryptstring2bytearray(self):
        text_start = "def\nhij\n"
        result_encrypted = PulseAppUtils.GPG_EncryptString2ByteArray(text_start, gpg_key_test)
        self.assertNotEqual(text_start.encode(), result_encrypted)
        path_testfile = os.path.join(path_testdir, "test.encryptstring2bytearray.temp.gpg")
        with open(path_testfile, 'wb') as f:
            f.write(result_encrypted)
        result_decrypted = PulseAppUtils.GPG_DecryptFile2String(path_testfile)
        self.assertEqual(text_start, result_decrypted)

    def test_gpg_encryptstring2bytearray_armor(self):
        text_start = "def\nhij\n"
        result_encrypted = PulseAppUtils.GPG_EncryptString2ByteArray(text_start, gpg_key_test, True)
        self.assertNotEqual(text_start.encode(), result_encrypted)
        path_testfile = os.path.join(path_testdir, "test.encryptstring2bytearray.armor.temp.gpg")
        with open(path_testfile, 'wb') as f:
            f.write(result_encrypted)
        result_decrypted = PulseAppUtils.GPG_DecryptFile2String(path_testfile)
        self.assertEqual(text_start, result_decrypted)


if __name__ == "__main__":
    unittest.main()

