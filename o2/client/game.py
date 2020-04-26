from asyncio import IncompleteReadError

from o2.handlers import gameHandlers

class client:

	def __init__(self, o2, reader, writer):
		self.o2 = o2

		self.streams = {}
		self.chars = {}
		self.player = {}

		self.player['string'] = None
		self.player['init_string'] = None #Used for reference when deciding how to execute savePlayerString()
		self.streams['reader'] = reader
		self.streams['writer'] = writer

		self.verified = False
		self.ip = self.getPeerIp()
		self.chars['null'] = b'\x00'

		#Track Packets
		self.handlers = gameHandlers.gameHandlers(o2, self)
		self.packet_history = []

	def getPeerIp(self):
		return(self.streams['writer'].get_extra_info('peername'))

	async def connect(self):
		#Verify the client is not already connected. If so, refuse connection.

		if(self.ip in self.o2.clients.keys()):
			self.o2.logging.log("client", ("game", self.ip, "bad_connection", "Client kicked from server. Multiple connections detected!"))
			await self.disconnect()
			return

		self.o2.clients[self.ip] = self
		self.o2.logging.log("client", ("game", self.ip, "new_connection", "A new client has connected! Active Clients: {%s}" % (str(len(self.o2.clients)))))

		while(not self.streams['writer'].is_closing()):
			try:
				data = await self.streams['reader'].readuntil(separator=self.chars['null'])
				if data:
					await self.readData(data)
				else:
					await self.disconnect()
			except IncompleteReadError:
				await self.disconnect()

	async def disconnect(self):
		extra = ""

		if("crossDomain" in self.packet_history):
			extra += "Will reconnect in a moment..."

		self.o2.logging.log("client", ("game", self.ip, "remv_client", "Client has been disconnected. " + extra))

		if self.ip in self.o2.clients.keys():
			self.o2.clients.pop(self.ip)

		if self.verified:
			await self.savePlayerString()
			self.o2.players.pop(self.player['id'])
			self.o2.rooms[self.player['room']].remove(self.player['id'])

			for remaining_player_id in self.o2.rooms[self.player['room']]:
				await self.o2.players[remaining_player_id].sendXt("rp", self.o2.roomInts[self.player['room']], self.player['id'])

			if self.player['buddies'] is not None and len(self.player['buddies']) > 0:
				for buddy_object in self.player['buddies']:
					try:
						buddy_id = int(buddy_object.split("|")[0])
						if buddy_id in self.o2.players:
							intRoom = "-1"
							if(self.player['room'] > 0):
								intRoom = self.o2.roomInts[self.player['room']]
							await self.o2.players[buddy_id].sendXt("bof", intRoom, self.player['id'])
					except ValueError:
						pass

		self.streams['writer'].close()

	async def disconnectWithError(self, error):
		if(await self.sendData(f"%xt%e%-1%{error}%")):
			await self.disconnect()

	async def readData(self, data):
		data = data.decode("utf-8")[:-1]
		self.o2.logging.log("client", ("game", self.ip, "data_received", data))

		if(data.startswith("<")):
			await self.handleData(data, type="xml")
		else:
			await self.handleData(data)

	async def handleData(self, data, type="xt"):
		if(type == "xml"):
			if("<policy-file-request/>" in data):
				self.packet_history.append("crossDomain")
				return await self.sendData("<cross-domain-policy><allow-access-from domain='*' to-ports='*' /></cross-domain-policy>")

			if("<body action='verChk' r='0'>" in data):
				self.packet_history.append("verChk")
				key = await self.o2.crypto.createRandomKey()
				return await self.sendData("<msg t='sys'><body action='apiOK' r='0'></body></msg>")

			if("<body action='rndK' r='-1'>" in data):
				self.packet_history.append("rndK")
				self.rndk = await self.o2.crypto.createRandomKey()
				return await self.sendData("<msg t='sys'><body action='rndK' r='-1'><k>%s</k></body></msg>" % self.rndk)

			if("<body action='login' r='0'><login z='w1'><nick>" in data):
				try:
					cdata = data.split("<")
					username = cdata[5][:-3][8:]
					key = cdata[8][:-3][8:]
					self.o2.logging.log("client", ("game", self.ip, "game", "Client {%s} is attempting to login..." % (username)))
					
					if(await self.verify(username, key)):
						self.player['username'] = username.title()
						self.player['id'] = await self.getPlayerId(self.player['username'])
						self.player['room'] = 0
						self.player['buddies'] = []
						self.o2.players[self.player['id']] = self
						self.verified = True

						self.o2.logging.log("client", ("game", self.ip, "game", "Client {%s} successfully verified. Joining server..." % (username)))

						await self.getPlayerString(build=True)
						await self.sendXt("l", "-1", "")
						#Client is now logged in. 
						
				except Exception as e:
					self.o2.logging.log("client", ("login", self.ip, "bad_packet", "An error occured processing client login information. Removing... Error Information: {%s}" % (str(e))))
					return await self.disconnect()

		if(type == "xt"):
			await self.handlers.handleXt(data)

	async def getPlayerId(self, username):
		player_id = await self.o2.db_conn.UserTable.select("id").where(self.o2.db_conn.UserTable.username == username).gino.scalar()
		return(player_id)

	async def getPlayerName(self, id):
		player_name = await self.o2.db_conn.UserTable.select("username").where(self.o2.db_conn.UserTable.id == id).gino.scalar()
		return(player_name)

	async def sendData(self, data):
		self.o2.logging.log("client", ("game", self.ip, "data_sent", data))
		data = data.encode('utf-8') + self.chars['null']
		self.streams['writer'].write(data)
		return True

	async def sendXt(self, *data):
		toSend = r"%xt%"

		for i in data:
			toSend += fr"{i}%"

		data = toSend

		self.o2.logging.log("client", ("game", self.ip, "data_sent", data))
		data = data.encode('utf-8') + self.chars['null']
		self.streams['writer'].write(data)
		return True

	async def sendRoomXt(self, *data):
		toSend = ""

		for i in data:
			toSend += fr"{i}%"

		toSend = toSend[:-1]

		try:
			for clientId in self.o2.rooms[self.player['room']]:
				clientObj = await self.o2.players[clientId].sendXt(toSend)
		except Exception as e:
			self.o2.logging.log("Exception Raised: {%s}" % (str(e)))

		return True

	async def verify(self, username, key):
		if(await self.verifyLoginKey(username, key)):
			return True

		return False

	async def verifyLoginKey(self, username, key):
		try:
			login_key = await self.o2.db_conn.UserTable.select("login_key").where(self.o2.db_conn.UserTable.username == username.title()).gino.scalar()
			rndk = self.rndk
			login_hash = await self.o2.crypto.createLoginHash(login_key, rndk)
			if(login_hash == key):
				return True
			else:
				self.o2.logging.log("client", ("game", self.ip, "game", "Client {%s} failed login key verification! Disconnecting..." % (username)))
				await self.disconnect()
				return False

		except Exception as e:
			self.o2.logging.log("client", ("game", self.ip, "game", "Client {%s} failed login key verification! Error Information: {%s}" % (username, e)))
			await self.disconnect()
			return False

	async def getPlayerString(self, build=False):
		"""
		Return a copy of the playerstring. Do not call DB functions unless actively refreshed.
		Database values will be updated from self.playerstring every N seconds using heartbeat packet. NO database functions here, just self.
		Only load from DB for initial playerstring
		"""

		#If player string is not set, load from DB, else load from local variables
		if(self.player['string'] is None or build == True):
			self.player['string'] = {
				"id" 		: self.player['id'],
				"username" 	: self.player['username'],
				"approval"	: 1,
				"color"		: await self.getCrumb("color"),
				"head"		: await self.getCrumb("head"),
				"face"		: await self.getCrumb("face"),
				"neck"		: await self.getCrumb("neck"),
				"body"		: await self.getCrumb("body"),
				"hand"		: await self.getCrumb("hand"),
				"feet"		: await self.getCrumb("feet"),
				"pin"		: await self.getCrumb("pin"),
				"background": await self.getCrumb("background"),
				"x"			: 0,
				"y"			: 0,
				"frame"		: 0,
				"membership": 1,
				"age"		: 2159, #mem age
			}

		self.player['init_string'] = self.player['string'].copy()

		return("|".join(map(str, self.player['string'].values())))

	async def savePlayerString(self, build=False):
		to_update = ["color", "head", "face", "neck", "body", "hand", "feet", "pin", "background"]
		
		for i in to_update:
			await self.saveCrumb(i)

	async def getCrumb(self, crumb):
		crumb_name = crumb
		crumb = await self.o2.db_conn.UserTable.select(crumb).where(self.o2.db_conn.UserTable.username == self.player['username']).gino.scalar()
		return(crumb)

	async def saveCrumb(self, crumb):
		crumb_name = crumb
		crumb_cont = self.player['string'][crumb_name]

		#Only re-update the DB if the string column is different from the initially loaded (on login) string
		if(self.player['init_string'][crumb_name] != self.player['string'][crumb_name]):
			kwargs = {crumb_name : crumb_cont}
			await self.o2.db_conn.UserTable.update.values(**kwargs).where(self.o2.db_conn.UserTable.id == self.player['id']).gino.status()

	async def getCoins(self):
		coins = await self.o2.db_conn.UserTable.select("coins").where(self.o2.db_conn.UserTable.username == self.player['username']).gino.scalar()
		self.player['coins'] = int(coins)
		return(coins)

	async def getInventory(self):
		items = await self.o2.db_conn.ItemTable.select("item_id").execution_options(model=None).where(self.o2.db_conn.ItemTable.player_id == self.player['id']).gino.all()
		items = [i[0] for i in items]
		return("%".join(map(str, items)))

	async def joinRoom(self, room_id, x = 0, y = 0):
		#try:

		room_id = int(room_id)
		old_room = self.player['room']

		#If client was in a previous room, remove him in o2 rooms{} as well as send the remaining players the rp packet
		if(old_room > 0):
			self.o2.rooms[old_room].remove(self.player['id'])
			for remaining_player_id in self.o2.rooms[old_room]:
				await self.o2.players[remaining_player_id].sendXt("rp", self.o2.roomInts[old_room], self.player['id'])

		self.player['room'] = room_id
		self.player['string']['x'] = x
		self.player['string']['y'] = y
		self.o2.rooms[room_id].append(self.player['id'])

		await self.sendXt("jr", self.o2.roomInts[room_id], room_id, await self.getRoomString(room_id))
		await self.sendRoomXt("ap", self.o2.roomInts[room_id], await self.getPlayerString())

		#except Exception as e:
		#	self.o2.logging.log("client", ("game", self.ip, "game", "User {%s} attempted to join an invalid room: {%s}" % (self.player['username'], str(e))))

	async def getRoomString(self, room_id):
		room_string = ""

		print(self.o2.rooms[room_id])

		for player_id in self.o2.rooms[room_id]:
			room_string += await self.o2.players[player_id].getPlayerString() + "%"

		return(room_string[:-1])

	async def addItem(self, item_id):
		try:
			item_id = int(item_id)
			if 0 < item_id <= 20000:
				item_exists =  await self.o2.db_conn.ItemTable.query.where(self.o2.db_conn.ItemTable.player_id == self.player['id']).where(self.o2.db_conn.ItemTable.item_id == item_id).gino.first()
				if item_exists is None:
						await self.sendXt("ai", self.o2.roomInts[self.player['room']], item_id, self.player['coins'])
						await self.saveItem(item_id)
						return
						
		except ValueError:
			pass

		print("You already have that item, or an unknown error occured") 
		return False

	#id|name|1 (0 for offline)
	#%xt%gb%2%105|Graph|0%
	async def getBuddies(self, refresh=False):
		buddies = await self.o2.db_conn.BuddyTable.select("buddy_id").execution_options(model=None).where(self.o2.db_conn.BuddyTable.player_id == self.player['id']).gino.all()
		buddy_ids = [i[0] for i in buddies]
		buddies = []

		for id in buddy_ids:
			toSend = ""
			toSend += str(id) + "|"
			toSend += await self.getPlayerName(id) + "|"
			if id in self.o2.players:
				
				#Online player condition
				toSend += "1"
				intRoom = "-1"
				if(self.verified):
					intRoom = self.o2.roomInts[self.player['room']]

				await self.o2.players[id].sendXt("bon", "-1", self.player['id'])

			else:
				toSend += "0"
			buddies.append(toSend)

		self.player['buddies'] = buddies

		if not refresh:
			return("%".join(map(str, buddies)))

	async def addBuddy(self, buddy_id):
		#Insert columns for buddy_id and our_id
		try:
			buddy_id = int(buddy_id)
			player_id = self.player['id']

			await self.o2.db_conn.BuddyTable.create(player_id=player_id, buddy_id=buddy_id)
			await self.o2.db_conn.BuddyTable.create(player_id=buddy_id, buddy_id=player_id)

		except (ValueError, IndexError):
			self.o2.logging.log("client", ("game", self.ip, "game", "User {%s} failed to add buddy. Error: {%s}" % (self.player['username'], str(e))))

	async def removeBuddy(self, buddy_id):
		#Remove columns for both
		try:
			buddy_id = int(buddy_id)
			player_id = self.player['id']

			await self.o2.db_conn.BuddyTable.delete.where(self.o2.db_conn.BuddyTable.player_id == player_id).where(self.o2.db_conn.BuddyTable.buddy_id == buddy_id).gino.status()
			await self.o2.db_conn.BuddyTable.delete.where(self.o2.db_conn.BuddyTable.player_id == buddy_id).where(self.o2.db_conn.BuddyTable.buddy_id == player_id).gino.status()
			#await self.o2.db_conn.BuddyTable.delete.where(self.o2.db_conn.BuddyTable.username == username).gino.scalar()

		except (ValueError, IndexError):
			self.o2.logging.log("client", ("game", self.ip, "game", "User {%s} failed to add buddy. Error: {%s}" % (self.player['username'], str(e))))

	async def saveItem(self, item_id):
		return await self.o2.db_conn.ItemTable.create(player_id=self.player['id'], item_id=item_id)