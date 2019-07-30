from spotlib._version import __version__ as version
from spotlib.statics import local_config


__author__ = 'Blake Huber'
__version__ = version
__email__ = "blakeca00@gmail.com"


try:
    from libtools import Colors
    from libtools import logd

    # global logger
    logd.local_config = local_config
    logger = logd.getLogger(__version__)

except Exception:
    pass


from spotlib.core import EC2SpotPrices

# instatiate spot price request object
retrieve = EC2SpotPrices()
