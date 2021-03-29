import asyncio
from config import Config
from server import Server
import GLOBALS

GLOBALS.CONFIG = Config()
GLOBALS.SERVER = Server('localhost', 7532)
GLOBALS.SERVER.start()