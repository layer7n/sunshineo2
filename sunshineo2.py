import asyncio
import sys
from datetime import datetime
import time

from o2.lib import logger, bootscreen, crypto, db
from o2.settings import settings
from o2.client import login, game
from o2.crumbs import buildCrumbs

class o2:

	def __init__(self, type):
		self.server = None
		self.server_type = type
		self.boot = bootscreen.bootscreen()
		self.boot.showBootScreen(type)
		self.crumbs = buildCrumbs.buildCrumbs()

		self.clients = {}	#self.clients[ip] = client_class
		self.players = {}	#self.players[id] = client_class
		self.rooms = {}		#self.rooms[room_id] = [list of player ID's in room] (of users in room)
		self.roomInts = {}	#self.roomInts[room_id] = room int ID

		self.logging = logger.logger()
		self.config = settings.config(self.logging).config
		self.logging.config = self.config['logging']
		self.crypto = crypto.crypto(length=8)

	async def serverLoop(self):
		await self.connectToDb()

		if(self.server_type == "login"):
			self.server = await asyncio.start_server(self.handleNewClient, self.config['login']['host'], self.config['login']['port'], start_serving=False)

			async with self.server:
				await self.server.start_serving()
				await self.server.serve_forever()

		elif(self.server_type == "game"):
			self.rooms = await self.crumbs.build(type="rooms")
			self.roomInts = await self.crumbs.build(type="room_ints")
			self.server = await asyncio.start_server(self.handleNewClient, self.config['game']['host'], self.config['game']['port'], start_serving=False)

			async with self.server:
				await self.server.start_serving()
				await self.server.serve_forever()

		else:
			self.logging.log("o2", "Invalid server type specified.")

	async def connectToDb(self):
		self.db_conn = db

		try:
			await self.db_conn.db.set_bind(f"postgresql://{self.config['db']['user']}:{self.config['db']['pass']}@{self.config['db']['host']}/{self.config['db']['db_name']}")
		except Exception as e:
			print()
			self.logging.log("o2", "Failed to connect to database. [Error Information]: {%s}" % (str(e)))
			print()
			sys.exit()
			return

		self.logging.logBoot("db", "Connected")
		self.boot.closeBootScreen()

	async def handleNewClient(self, reader, writer):
		type = self.server_type

		if(type == "login"):
			await login.client(self, reader, writer).connect()
			
		elif(type == "game"):
			await game.client(self, reader, writer).connect()

	async def getCurrentTime(self):
		return datetime.now()

	async def getCurrentTimeSeconds(self):
		return time.time()