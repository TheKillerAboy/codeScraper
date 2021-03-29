import asyncio
import threading

import socketio

import GLOBALS
from sanic import Sanic


class Server(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.loop = asyncio.get_event_loop()

        self.sio = socketio.AsyncServer(async_mode='sanic', cors_allowed_origins=[],async_handlers=True)
        self.app = Sanic(__name__)
        self.app.config['CORS_SUPPORTS_CREDENTIALS'] = True
        self.sio.attach(self.app)

        self.host = host
        self.port = port

        self.init_routes()
        self.init_sockets()

    def init_routes(self):
        pass

    def init_sockets(self):
        @self.sio.event
        async def connect(sid, environ):
            print('connect ', sid)

        @self.sio.event
        async def disconnect(sid):
            print('disconnect ', sid)

        @self.sio.on('update root folder', namespace='/root-folder')
        async def update_root_folder(sid, data):
            if data['change']:
                GLOBALS.CONFIG['contest-root-folder'] = await GLOBALS.GUI.filedialog_askdirectory()
            await self.sio.emit('updated root folder', {'contest-root-folder':GLOBALS.CONFIG['contest-root-folder']}, namespace='/root-folder')
            GLOBALS.CONFIG.save()

    def run(self):
        self.app.run(self.host, self.port)