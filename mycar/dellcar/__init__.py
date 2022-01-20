import os

import pkg_resources  # part of setuptools
import sys

# __version__ = pkg_resources.require("dellcar")[0].version
# print('using dell version: {} ...'.format(__version__))
print("wait a minute")


current_module = sys.modules[__name__]


if sys.version_info.major < 3:
    msg = 'Dell_car Requires Python 3.4 or greater. You are using {}'.format(sys.version)
    raise ValueError(msg)

from . import parts
from .vehicle import Vehicle
from .memory import Memory
from . import util
from . import config
from .config import load_config
