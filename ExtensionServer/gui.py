import asyncio
import tkinter
from tkinter import filedialog


class Gui:
    def __init__(self):
        self.tk = tkinter.Tk()
        self.tk.withdraw()

        self.being_inserted = False
        self.queue_insert = {}
        self.run_in_loop = {}
        self.being_removed = False
        self.queue_remove = []

    async def insert_event(self, name, method, *args, **kwargs):
        while self.being_inserted:
            await asyncio.sleep(0.1)
        self.being_inserted = True
        self.queue_insert[name] = {
            'method': method,
            'args': args,
            'kwargs': kwargs
        }
        self.being_inserted = False

    async def remove_event(self, name):
        while self.being_removed:
            await asyncio.sleep(0.1)
        self.being_removed = True
        self.queue_remove.append(name)
        self.being_removed = False

    def __filedialog_askdirectory(self, ref, **options):
        ref['out'] = filedialog.askdirectory(**options)
        self.queue_remove.append('filedialog_askdirectory')

    async def filedialog_askdirectory(self, **options):
        ref = {'out':0}
        await self.insert_event('filedialog_askdirectory', self.__filedialog_askdirectory, ref, **options)
        while ref['out'] == 0:
            await asyncio.sleep(0.1)
        return ref['out']

    def run(self):
        while True:
            if not self.being_inserted:
                self.being_inserted = True
                for key, value in self.queue_insert:
                    self.run_in_loop[key] = value
                self.queue_insert.clear()
                self.being_inserted = False

            for event in self.run_in_loop.values():
                event['method'](*event['args'], **event['kwargs'])

            if not self.being_removed:
                self.being_removed = True
                for event_name in self.queue_remove:
                    del self.run_in_loop[event_name]
                self.queue_remove.clear()
                self.being_removed = False
