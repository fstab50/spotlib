from spotlib._version import __version__ as version
from spotlib.statics import local_config

try:
    from libtools import Colors
    from libtools import logd
except Exception:
    pass


__author__ = 'Blake Huber'
__version__ = version
__email__ = "blakeca00@gmail.com"


# global logger
logd.local_config = local_config
logger = logd.getLogger(__version__)
