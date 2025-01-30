import asyncio
from nats.aio.client import Client as NATS
from utils import print_info, print_success, print_error

class Broker:
    
    def __init__(self):
        self._nc = NATS()
        
    async def connect(self, url):
        print_info("Connecting to NATs Server")
        await self._nc.connect(url)
        print_success("Connection successfully to NATs Server")
        
    async def subscribe(self, topic, callback):
        await self._nc.subscribe(topic, cb=callback)
        
    async def publish(self, topic, data):
        await self._nc.publish(topic, data)
        
    async def drain(self):
        await self._nc.drain()