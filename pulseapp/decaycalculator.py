import sys
import os 
import logging

_logging_format="%(funcName)s: %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"
logging.basicConfig(stream=sys.stderr, format=_logging_format, datefmt=_logging_datetime)

log = logging.getLogger('pulse')
log.setLevel(logging.DEBUG)

class DecayCalculator(object):

    def TotalQtyForDay(when, data_dt, data_qty):
        log.debug("when=(%s)\n\tdata_dt=(%s)\n\tdata_qty=(%s)" % (str(when), str(data_dt), str(data_qty)))
        return 0

    def CalculateQtyAtDT(when, data_dt, data_qty, halflife, onset):
        log.debug("when=(%s)\n\tdata_dt=(%s)\n\tdata_qty=(%s)\n\thalflife=(%s)\n\tonset=(%s)" % (str(when), str(data_dt), str(data_qty), str(halflife), str(onset)))
        return 0


