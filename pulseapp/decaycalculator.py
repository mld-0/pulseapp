#   VIM SETTINGS: {{{3
#   vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#   vim: set foldlevel=2 foldcolumn=1:
#   }}}1
import sys
import os 
import logging
import datetime
from decimal import Decimal
from pulseapp.utils import PulseAppUtils
#   {{{2
_logging_format="%(funcName)s: %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"
logging.basicConfig(stream=sys.stderr, format=_logging_format, datefmt=_logging_datetime)

log = logging.getLogger('pulse')
log.setLevel(logging.DEBUG)

class DecayCalculator(object):

    threshold_halflife_count = 16

    @staticmethod
    def TotalQtyForDay(when, data_datetimes, data_qtys):
        """Get total qty in list for a given day"""
    #   {{{
        log.debug("when=(%s)\n\tlen(data_datetimes)=(%s)\n\tlen(data_qtys)=(%s)" % (str(when), str(len(data_datetimes)), str(len(data_qtys))))
        result_sum = Decimal(0.0)
        day_start, day_end = PulseAppUtils._DayStartAndEndTimes_FromDate(when)
        for loop_dt, loop_qty in zip(data_datetimes, data_qtys):
            #   reconcile timezones
            #   {{{
            if (loop_dt.tzinfo is None) and (day_start.tzinfo is not None):
                loop_dt = loop_dt.replace(tzinfo = day_start.tzinfo)
            if (day_start.tzinfo is None) and (loop_dt.tzinfo is not None):
                day_start = day_start.replace(tzinfo = loop_dt.tzinfo)
            if (day_end.tzinfo is None) and (loop_dt.tzinfo is not None):
                day_end = day_end.replace(tzinfo = loop_dt.tzinfo)
            #   }}}
            if (loop_dt >= day_start) and (loop_dt <= day_end):
                result_sum += Decimal(loop_qty)
        return result_sum
    #   }}}

    @staticmethod
    def CalculateQtyAtDT(when, data_datetimes, data_qtys, halflife, onset):
        """given lists data_qtys/data_datetimes (assuming expodential decay of halflife and linear onset of onset), find the qty remaining at when"""
    #   {{{
        log.debug("when=(%s)\n\tlen(data_datetimes)=(%s)\n\tlen(data_qtys)=(%s)\n\thalflife=(%s)\n\tonset=(%s)" % (str(when), str(len(data_datetimes)), str(len(data_qtys)), str(halflife), str(onset)))
        _startime = datetime.datetime.now()
        log.debug(f"when=({when})")
        result_qty = Decimal(0.0)
        for loop_dt, loop_qty in zip(data_datetimes, data_qtys):
            #   Reconcile timezones 
            #   {{{
            if (loop_dt.tzinfo is None) and (when.tzinfo is not None):
                loop_dt = loop_dt.replace(tzinfo = when.tzinfo)
            elif (when.tzinfo is None) and (loop_dt.tzinfo is not None):
                when = when.replace(tzinfo = loop_dt.tzinfo)
            #   }}}
            #   get difference between when and loop_dt in seconds
            loop_delta_s = (when - loop_dt).total_seconds()
            if (loop_delta_s > halflife * DecayCalculator.threshold_halflife_count):
                continue
            loop_result_qty = Decimal(0.0)
            if (loop_delta_s > onset) and (loop_delta_s < halflife * DecayCalculator.threshold_halflife_count):
                loop_hl_fraction = (loop_delta_s - onset) / halflife
                loop_result_qty = loop_qty * Decimal(0.5) ** Decimal(loop_hl_fraction)
            elif (loop_delta_s > 0) and (loop_delta_s < halflife * DecayCalculator.threshold_halflife_count):
                loop_result_qty = loop_qty * Decimal(loop_delta_s / onset)

            #if (loop_result_qty > 0):
            #    log.debug(f"loop_delta_s=({loop_delta_s})")
            #    log.debug(f"loop_qty=({loop_qty})")
            #    log.debug(f"loop_result_qty=({loop_result_qty})")

            result_qty += loop_result_qty
        _timedone = datetime.datetime.now()
        _elapsed = _timedone - _startime
        log.debug("_elapsed=(%s)" % str(_elapsed))
        return result_qty
    #   }}}


