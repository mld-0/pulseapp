#   VIM SETTINGS: {{{3
#   vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#   vim: set foldlevel=2 foldcolumn=1:
#   }}}1
import sys
import os 
import logging
import time
import pandas
import datetime
import pprint
import hashlib
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from subprocess import Popen, PIPE
#   {{{2

_logging_format="%(funcName)s: %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"
logging.basicConfig(stream=sys.stderr, format=_logging_format, datefmt=_logging_datetime)

log = logging.getLogger('pulse')
log.setLevel(logging.DEBUG)

class PulseAppUtils(object):

    @staticmethod
    def _DayStartAndEndTimes_FromDate(arg_day):
        """For a given date, return as python datetime [ first, last ] second of that day"""
    #   {{{
        if not isinstance(arg_day, datetime.datetime):
            arg_day = dateparser.parse(arg_day)
        result_start = arg_day.replace(hour=0, minute=0, second=0, microsecond=0)
        result_end = arg_day.replace(hour=23, minute=59, second=59, microsecond=0)
        return [ result_start, result_end ]
    #   }}}

    #   Ongoing: 2021-07-30T14:48:13AEST pulseapp, optimisation, decryption is the slowest part, store contents of decrypted files and use that text for each call to ReadTimestampedQtyScheduleData() provided the file hasn't changed
    @staticmethod
    def ReadTimestampedQtyScheduleData(filepaths, label, data_cols, data_delim):
        """Read qtys (Decimals) and timestamps (datetimes) corresponding to given label (or all entries if None) for each file in filepaths, and return (timestamps, qtys)"""
        #   {{{
        log.debug("filepaths=(%s)\n\tlabel=(%s)\n\tdata_cols=(%s)\n\tdata_delim=(%s)" % (str(filepaths), label, str(data_cols), data_delim))
        results_datetime = []
        results_qty = []
        for loop_filepath in filepaths:
            loop_filestr = PulseAppUtils.GPG_DecryptFile2String(loop_filepath)
            for loop_line in loop_filestr.split("\n"):
                loop_line_split = loop_line.split(data_delim)
                if len(loop_line.strip()) == 0:
                    continue
                if len(loop_line_split) <= 1:
                    log.warning("len(loop_line_split)=(%s), loop_line_split=(%s)" % (len(loop_line_split), loop_line_split))
                    continue
                if label is None or loop_line_split[data_cols['label']] == label:
                    loop_qty_str = loop_line_split[data_cols['qty']]
                    loop_qty = Decimal(loop_qty_str)
                    loop_datetime_str = loop_line_split[data_cols['datetime']]
                    loop_datetime = PulseAppUtils._ParseScheduleDatetime(loop_datetime_str)
                    if loop_datetime is None:
                        raise Exception("loop_datetime is None for loop_datetime_str=(%s)" % (loop_datetime_str))
                    results_datetime.append(loop_datetime)
                    results_qty.append(loop_qty)
        log.debug("len=(%s)" % str(len(results_datetime)))
        assert len(results_datetime) == len(results_qty)
        return (results_datetime, results_qty)
        #   }}}

    @staticmethod
    def _ParseScheduleDatetime(arg_datetime_str):
        """Convert string either in 'dts' or iso format to datetime"""
        #   {{{
        result_datetime = None
        parse_formats = [ "(%Y-%m-%d)-(%H-%M-%S)", "%Y-%m-%dT%H:%M:%S%Z", "%Y-%m-%dT%H:%M:%S" ]
        for loop_format in parse_formats:
            try:
                result_datetime = datetime.datetime.strptime(arg_datetime_str, loop_format)
            except Exception as e:
                pass
            if result_datetime is not None:
                return result_datetime
        return None
        #   }}}


    @staticmethod
    def MonthlyDateRange_FromFirstAndLast(arg_dt_first, arg_dt_last, arg_includeMonthBefore=False, arg_result_str=True):
        """Get list of months between two dates, as either strings or datetimes. Optionally include month before first date."""
    #   {{{
        if (isinstance(arg_dt_first, str)):
            arg_dt_first = dateparser.parse(arg_dt_first)
        if (isinstance(arg_dt_last, str)):
            arg_dt_last = dateparser.parse(arg_dt_last)
        arg_dt_first = arg_dt_first.replace(day=1, hour=0, minute=0, second=0)
        arg_dt_last = arg_dt_last.replace(day=1, hour=23, minute=59, second=59)
        if (arg_dt_first > arg_dt_last):
            raise Exception("Invalid arg_dt_first=(%s) > arg_dt_last=(%s)" % (str(arg_dt_first), str(arg_dt_last)))
        _dt_format_convertrange = '%Y-%m-%dT%H:%M:%S%Z'
        _dt_format_output = '%Y-%m'
        _dt_freq = 'MS'
        log.debug("arg_includeMonthBefore=(%s)" % str(arg_includeMonthBefore))
        if (arg_includeMonthBefore):
            arg_dt_beforeFirst = arg_dt_first + relativedelta(months=-1)
            arg_dt_beforeFirst = arg_dt_beforeFirst.replace(day=1)
            arg_dt_first = arg_dt_beforeFirst
        #log.debug("arg_dt_first=(%s)" % str(arg_dt_first))
        #log.debug("arg_dt_last=(%s)" % str(arg_dt_last))
        dt_Range = [ x.to_pydatetime() for x in pandas.date_range(start=arg_dt_first.strftime(_dt_format_convertrange), end=arg_dt_last.strftime(_dt_format_convertrange), freq=_dt_freq) ]
        if (arg_result_str):
            datetime_range_strings = [ x.strftime(_dt_format_output) for x in dt_Range ]
            log.debug("datetime_range_strings=(%s)" % str(datetime_range_strings))
            return datetime_range_strings
        else:
            log.debug("dt_Range=(%s)" % str(dt_Range))
            return dt_Range
    #   }}}

    #   TODO: 2021-01-26T11:41:37AEDT Compare sh256 of resulting string to sh256 of decrypted existing file, skip copying if match
    @staticmethod
    def CopyLogDataFile_DivideByMonth(arg_source_path, arg_dest_dir, arg_dest_prefix, arg_dest_postfix, arg_dt_first, arg_dt_last, arg_overwrite=False, arg_includeMonthBefore=False, arg_gpg_key=None, arg_remove_duplicate_lines=True):
        """Copy lines from single source file arg_source_path to file(s) in arg_dest_dir, for range of months, copying lines containing given month to destination file for said month. Optionally encrypt data with system gpg. If arg_remove_duplicate_lines is True, do not copy any lines that are duplicates of those already seen during copying."""
    #   {{{
        log.debug( "arg_source_path=(%s)\n\targ_dest_dir=(%s)\n\targ_dest_prefix=(%s)\n\targ_dest_postfix=(%s)\n\targ_dt_first=(%s)\n\targ_dt_last=(%s)\n\targ_overwrite=(%s)\n\targ_includeMonthBefore=(%s)\n\targ_gpg_key=(%s)\n\targ_remove_duplicate_lines=(%s)" % (arg_source_path, arg_dest_dir, arg_dest_prefix, arg_dest_postfix, arg_dt_first, arg_dt_last, arg_overwrite, arg_includeMonthBefore, arg_gpg_key, arg_remove_duplicate_lines))
        _starttime = datetime.datetime.now()
        #datetime_range_strings = TimePlotUtils.MonthlyDateRange_FromFirstAndLast(arg_dt_first, arg_dt_last, arg_includeMonthBefore, True)
        datetime_range_strings = PulseAppUtils.MonthlyDateRange_FromFirstAndLast(arg_dt_first, arg_dt_last, arg_includeMonthBefore, True)

        for loop_date_str in datetime_range_strings:
            loop_data = ""
            with open(arg_source_path, "r") as f:
                for loop_line in f:
                    loop_line = loop_line.strip()
                    #   If loop_line contains loop_date_str, append it to loop_data
                    if not loop_line.find(loop_date_str) == -1:
                        if (arg_remove_duplicate_lines):
                            loop_data_lineslist = loop_data.split('\n')
                            if loop_line in loop_data_lineslist:
                                log.debug("skip duplicate, loop_line=(%s)" % str(loop_line))
                                continue
                        loop_data += loop_line + '\n'

            log.debug("loop_date_str=(%s) lines(loop_data)=(%s)" % (str(loop_date_str), len(loop_data.split('\n'))))
            loop_dest_filename = arg_dest_prefix + loop_date_str + arg_dest_postfix
            loop_dest_filepath = os.path.join(arg_dest_dir, loop_dest_filename)
            log.debug("loop_dest_filename=(%s)" % str(loop_dest_filename))

            #   GPG encryption is fast, decryption is slow (and since files are not being written to dropbox, who cares if they are constantly being updated?) 
            ##   Compare hash of (decrypted) existing file to hash of text to be written to new file, skip if matching
            #loop_sha256_existing_file_contents = ""
            #loop_sha256_new_file_contents = ""
            #if os.path.isfile(loop_dest_filepath):
            #    loop_existing_file_text = PulseAppUtils.GPG_DecryptFile2String(loop_dest_filepath)
            #    loop_sha256_existing_file_contents = hashlib.sha256(loop_existing_file_text.encode()).hexdigest()
            #loop_sha256_new_file_contents = hashlib.sha256(loop_data.encode()).hexdigest()
            #log.debug("loop_sha256_existing_file_contents=(%s)" % loop_sha256_existing_file_contents)
            #log.debug("loop_sha256_new_file_contents=(%s)" % loop_sha256_new_file_contents)
            #if (loop_sha256_existing_file_contents == loop_sha256_new_file_contents):
            #    log.debug("hashes match, skip update")
            #    continue

            if os.path.isfile(loop_dest_filepath) and not arg_overwrite:
                log.debug("skip write, arg_overwrite=(%s)" % str(arg_overwrite))
                continue

            #   Write loop_data to loop_dest_filepath, either as text or gpg encrypted data
            if not (arg_gpg_key is None):
                loop_data_enc = PulseAppUtils.GPG_EncryptString2ByteArray(loop_data, arg_gpg_key, False)
                with open(loop_dest_filepath, "wb") as f:
                    f.write(loop_data_enc)
            else:
                with open(loop_dest_filepath, "w") as f:
                    f.write(loop_data)

        _timedone = datetime.datetime.now()
        _elapsed = _timedone - _starttime
        log.debug("_elapsed=(%s)" % str(_elapsed))
    #   }}}

    #@staticmethod
    #def GetAvailableFiles_FromMonthlyRange(path_dir, prefix, postfix, month_start, month_end, includeMonthBefore):
    #    log.debug("path_dir=(%s)\n\tprefix=(%s)\n\tpostfix=(%s)\n\tmonth_start=(%s)\n\tmonth_end=(%s)\n\tincludeMonthBefore=(%s)" % (path_dir, prefix, postfix, month_start, month_end, includeMonthBefore))

    @staticmethod
    def GetFiles_FromMonthlyRange(arg_data_dir, arg_file_prefix, arg_file_postfix, arg_dt_first, arg_dt_last, arg_includeMonthBefore=False):
        """Get a list of the files in arg_data_dir, where each file is of the format 'arg_file_prefix + date_str + arg_file_postfix', and date_str is %Y-%m for each year and month between one month before arg_dt_first, and arg_dt_last"""
    #   {{{ 
        log.debug("arg_data_dir=(%s)\n\targ_file_prefix=(%s)\n\targ_file_postfix=(%s)\n\targ_dt_first=(%s)\n\targ_dt_last=(%s)\n\targ_includeMonthBefore=(%s)" % (arg_data_dir, arg_file_prefix, arg_file_postfix, arg_dt_first, arg_dt_last, arg_includeMonthBefore))
        #datetime_range_strings = TimePlotUtils.MonthlyDateRange_FromFirstAndLast(arg_dt_first, arg_dt_last, arg_includeMonthBefore, True)
        datetime_range_strings = PulseAppUtils.MonthlyDateRange_FromFirstAndLast(arg_dt_first, arg_dt_last, arg_includeMonthBefore, True)
        #   Raise exception if arg_data_dir doesn't exist
        if not os.path.isdir(arg_data_dir):
            raise Exception("dir not found arg_data_dir=(%s)" % str(arg_data_dir))
        #   Get list of files of format 'arg_file_prefix + date_str + arg_file_postfix' which exist, with warning for those which don't. Raise exception if no files are found
        located_filepaths = []
        for loop_date_str in datetime_range_strings:
            loop_candidate_filename = arg_file_prefix + loop_date_str + arg_file_postfix
            log.debug("loop_candidate_filename=(%s)" % str(loop_candidate_filename))
            loop_candidate_filepath = os.path.join(arg_data_dir, loop_candidate_filename)
            if os.path.isfile(loop_candidate_filepath):
                located_filepaths.append(loop_candidate_filepath)
        log.debug("located_filepaths:\n%s" % pprint.pformat(located_filepaths))
        if len(located_filepaths) == 0:
            raise Exception("no files located")
        return located_filepaths
    #   }}}

    @staticmethod
    def GPG_DecryptFile2String(path_file):
        """Given a path to gpg encrypted file, decrypt file using system gpg/keychain, raise Exception if file is not decryptable, or if it doesn't exist. Note: output may have a newline added to end."""
    #   {{{
        t_start = time.time()
        log.debug("file=(%s)" % str(os.path.basename(path_file)))
        cmd_gpg_decrypt = ["gpg", "-q", "--decrypt", path_file ]
        log.debug("cmd_gpg_decrypt=(%s)" % str(cmd_gpg_decrypt))
        p = Popen(cmd_gpg_decrypt, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        result_data_decrypt, result_stderr = p.communicate()
        result_str = result_data_decrypt.decode()
        result_stderr = result_stderr.decode()
        rc = p.returncode
        if (rc != 0):
            raise Exception("gpg decrypt non-zero returncode=(%s), result_stderr=(%s), result_str=(%s)" % (str(rc), str(result_stderr), str(result_str)))
        t_end = time.time()
        t_elapsed = round(t_end - t_start, 2)
        log.debug("decrypt dt=(%s)" % str(t_elapsed))
        log.debug("result_stderr=(%s)" % str(result_stderr))
        log.debug("lines=(%s)" % str(result_str.count("\n")))
        return result_str
    #   }}}

    @staticmethod
    def GPG_EncryptString2ByteArray(input_text, gpg_key_id, ascii_armor=False):
        """Take a string, encrypt that string with the system gpg keychain, and return result as a bytearray"""
    #   {{{
        t_start = time.time()
        #   convert string(input_text) -> bytearray(cmd_encrypt_input)
        cmd_encrypt_input = bytearray()
        cmd_encrypt_input.extend(input_text.encode())
        #   gpg encrypt arguments
        cmd_gpg_encrypt = [ "gpg", "-o", "-", "-q", "--encrypt", "--recipient", gpg_key_id ]
        if (ascii_armor == True):
            cmd_gpg_encrypt.append("--armor")
        #   Use Popen, call cmd_gpg_encrypt, using PIPE for stdin/stdout/stderr
        log.debug("cmd_gpg_encrypt=(%s)" % str(cmd_gpg_encrypt))
        p = Popen(cmd_gpg_encrypt, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        result_data_encrypt, result_stderr = p.communicate(input=cmd_encrypt_input)
        result_stderr = result_stderr.decode()
        rc = p.returncode
        if (rc != 0):
            raise Exception("Failed to encrypt, rc=(%s)" % str(rc))
        t_end = time.time()
        t_elapsed = round(t_end - t_start, 2)
        #   printdebug:
        log.debug("encrypt dt=(%s)" % (str(t_elapsed)))
        log.debug("result_stderr=(%s)" % str(result_stderr))
        log.debug("input_text_len=(%s)" % str(len(input_text)))
        log.debug("result_data_encrypt_len=(%s)" % str(len(result_data_encrypt)))
        return result_data_encrypt
    #   }}}


