from aiohttp import web
import socketio

class SocIO:
    def __init__(self):
        self.init_routes()
        self.init_sockets()

    def init_routes(self):
        async def index(request):
            return

    def init_sockets(self):
        pass