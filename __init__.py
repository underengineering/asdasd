
import logging
from typing import Dict, Type

from asyncraft.proto import Protocol
from asyncraft.proto.packets import *
from asyncraft.proto.packet import Packet
from asyncraft.utils import Version

logging.basicConfig(level = logging.DEBUG)
