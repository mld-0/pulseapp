import logging
import sys
from .pulse import PulseApp

_logging_format="%(funcName)s: %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"

logging.basicConfig(stream=sys.stderr)
log = logging.getLogger('pulse')
log.setLevel(level=logging.DEBUG)

if __name__ == '__main__':
    log.debug("__main__")
    app = PulseApp()
    app.run()

