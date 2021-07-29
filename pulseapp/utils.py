import sys
import os 
import logging

_logging_format="%(funcName)s: %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"
logging.basicConfig(stream=sys.stderr, format=_logging_format, datefmt=_logging_datetime)

log = logging.getLogger('pulse')
log.setLevel(logging.DEBUG)

class PulseUtils(object):

    @staticmethod
    def ReadQtyScheduleData(filepaths, label):
        log.debug("filepaths=(%s), label=(%s)" % (str(filepaths), label))
        return (None, None)

    @staticmethod
    def CopyLogDataFile_DivideByMonth(path_source, dir_copy, copy_prefix, copy_postfix, month_start, month_end, overwrite, includeMonthBefore, gpgkey, remove_duplicates):
        log.debug("path_source=(%s)\n\tdir_copy=(%s)\n\tcopy_prefix=(%s)\n\tcopy_postfix=(%s)\n\tmonth_start=(%s)\n\tmonth_end=(%s)\n\toverwrite=(%s)\n\tincludeMonthBefore=(%s)\n\tgpgkey=(%s)\n\tremove_duplicates=(%s)" % (path_source, dir_copy, copy_prefix, copy_postfix, month_start, month_end, overwrite, includeMonthBefore, gpgkey, remove_duplicates))

    @staticmethod
    def GetAvailableFiles_FromMonthlyRange(path_dir, prefix, postfix, month_start, month_end, includeMonthBefore):
        log.debug("path_dir=(%s)\n\tprefix=(%s)\n\tpostfix=(%s)\n\tmonth_start=(%s)\n\tmonth_end=(%s)\n\tincludeMonthBefore=(%s)" % (path_dir, prefix, postfix, month_start, month_end, includeMonthBefore))


