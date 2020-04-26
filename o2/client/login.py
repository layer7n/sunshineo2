from asyncio import IncompleteReadError

class client:

	def __init__(self, o2, reader, writer):
		self.o2 = o2
		self.streams = {}
		self.chars = {}
		self.player = {}

		self.streams['reader'] = reader
		self.streams['writer'] = writer

		self.ip = self.getPeerIp()
		self.chars['null'] = b'\x00'

		#Track Packets
		self.packet_history = []

	def getPeerIp(self):
		return(self.streams['writer'].get_extra_info('peername'))

	async def connect(self):
		#Verify the client is not already connected. If so, refuse connection.

		if(self.ip in self.o2.clients.keys()):
			self.o2.logging.log("client", ("login", self.ip, "bad_connection", "Client kicked from server. Multiple connections detected!"))
			await self.disconnect()
			return

		self.o2.clients[self.ip] = self
		self.o2.logging.log("client", ("login", self.ip, "new_connection", "A new client has connected! Active Clients: {%s}" % (str(len(self.o2.clients)))))

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

		self.o2.logging.log("client", ("login", self.ip, "remv_client", "Client has been disconnected. " + extra))

		if self.ip in self.o2.clients.keys():
			self.o2.clients.pop(self.ip)

		self.streams['writer'].close()

	async def disconnectWithError(self, error):
		if(await self.sendData(f"%xt%e%-1%{error}%")):
			await self.disconnect()

	async def readData(self, data):
		data = data.decode("utf-8")[:-1]
		self.o2.logging.log("client", ("login", self.ip, "data_received", data))

		if(data.startswith("<")):
			await self.handleData(data, type="xml")

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
				#try:
				cdata = data.split("<")
				username = cdata[5][:-3][8:]
				password = cdata[8][:-3][8:]
				self.o2.logging.log("client", ("login", self.ip, "login", "Client {%s} is attempting to login..." % (username)))
				
				if(await self.verify(username, password)):
					self.player['username'] = username.title()
					self.player['id'] = await self.getPlayerId(self.player['username'])
					await self.insertLogin(self.player['id'], self.player['username'], self.ip)
					self.o2.logging.log("client", ("login", self.ip, "login", "Client {%s} successfully verified!" % (self.player['username'])))

					#Client verification complete. Proceed to login.
					#[%xt%l%-1%$ID%" . $this->makeLoginKey($name) . "%%" . $slist]
					#self.sendXt("l", user.ID, loginKey, "|".join(buddyWorlds), "|".join(worldPopulations))
					#%xt%l%-1%101%bfcb504aaa59600cb4bc6be94567c692%%100,0%
					self.login_key = await self.handleLoginKey()
					await self.sendXt("l", "-1", self.player['id'], self.login_key, "", "100,0")

				#except Exception as e:
				#	self.o2.logging.log("client", ("login", self.ip, "bad_packet", "An error occured processing client login information. Removing... Error Information: {%s}" % (str(e))))
				#	return await self.disconnect()

	async def getPlayerId(self, username):
		player_id = await self.o2.db_conn.UserTable.select("id").where(self.o2.db_conn.UserTable.username == username).gino.scalar()
		return(player_id)

	async def insertLogin(self, id, username, ip):
		i = {}
		i['id'] = id
		i['username'] = username
		i['timestamp'] = await self.o2.getCurrentTime()
		i['ip'] = ip[0]

		return await self.o2.db_conn.LoginTable.create(player_id=i['id'], username=i['username'], timestamp=i['timestamp'], ip=i['ip'])

	async def sendData(self, data):
		self.o2.logging.log("client", ("login", self.ip, "data_sent", data))
		data = data.encode('utf-8') + self.chars['null']
		self.streams['writer'].write(data)
		return True

	async def sendXt(self, *data):
		toSend = r"%xt%"

		for i in data:
			toSend += fr"{i}%"

		data = toSend

		self.o2.logging.log("client", ("login", self.ip, "data_sent", data))
		data = data.encode('utf-8') + self.chars['null']
		self.streams['writer'].write(data)
		return True

	async def verify(self, username, password):
		if(await self.verifyHandshake()):
			if(await self.verifyCredentials(username, password)):
				return True

		return False

	async def verifyHandshake(self):
		toCheck = ["verChk", "rndK"]
		for i in toCheck:
			if i not in self.packet_history:
				self.o2.logging.log("client", ("login", self.ip, "bad_packet", "Client failed handshake! Disconnecting... Packets Missing: {%s}" % (i)))
				await self.disconnect()
				return False
		return True

	async def verifyCredentials(self, username, password):
		if(len(username) < 1 or len(username) > 16):
			self.o2.logging.log("client", ("login", self.ip, "credentials", "Client entered an invalid username length. Removing..."))
			await self.disconnect()
			return False 

		if(len(password) < 1 or len(password) > 64):
			self.o2.logging.log("client", ("login", self.ip, "credentials", "Client entered an invalid password length. Removing..."))
			await self.disconnect()
			return False 

		if(not await self.userExists(username)):
			self.o2.logging.log("client", ("login", self.ip, "credentials", "Client account does not exist!"))
			await self.disconnectWithError(100)
			return False

		if(not await self.passMatch(username, password)):
			self.o2.logging.log("client", ("login", self.ip, "credentials", "Client incorrect password!"))
			await self.disconnectWithError(101)
			return False

		return True

	async def userExists(self, username):
		user = await self.o2.db_conn.UserTable.query.where(self.o2.db_conn.UserTable.username == username.title()).gino.first()
		if user:
			return True
		return False

	async def passMatch(self, username, password): #Returns true if pass matches pass in DB
		try:
			realPass = await self.o2.crypto.formatHash(await self.o2.db_conn.UserTable.select("password").where(self.o2.db_conn.UserTable.username == username.title()).gino.scalar(), self.rndk)
			
			if(realPass != password):
				return False
			return True

		except Exception as e:
			self.o2.logging.log("client", ("login", self.ip, "invalid_pass", "An error occured processing client login information. Removing... Error Information: {%s}" % (str(e))))
			await self.disconnect()
			return False

	async def handleLoginKey(self):
		key = await self.o2.crypto.createLoginKey(self.rndk)
		await self.o2.db_conn.UserTable.update.values(login_key=key).where(self.o2.db_conn.UserTable.id == self.player['id']).gino.status()
		return key