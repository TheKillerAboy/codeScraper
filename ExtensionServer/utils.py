import asyncio
import sys
from pathlib import Path as PATH
from concurrent.futures import ThreadPoolExecutor


class Path:
    if getattr(sys, 'frozen', False):
        BASE = PATH(sys._MEIPASS)
    else:
        BASE = PATH(sys.argv[0]) / '..'
    CONFIG = BASE/'config.yaml'

class Async:
    _executor = ThreadPoolExecutor(10)
    @classmethod
    async def in_thread(cls, func):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(cls._executor, func)