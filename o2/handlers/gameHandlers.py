from o2.lib import commands

class gameHandlers:

	#Max per second, -1 cooldown specifies can only be sent once

	spam_cooldown = 0.5 #

	throttle = { 
		"u#h"  : {"cooldown" : 59},
		"m#sm" : {"cooldown" : spam_cooldown},
		"u#sp" : {"cooldown" : spam_cooldown},
		"u#sf" : {"cooldown" : spam_cooldown},
		"u#ss" : {"cooldown" : spam_cooldown},
		"u#sq" : {"cooldown" : spam_cooldown},
		"u#sa" : {"cooldown" : spam_cooldown},
		"u#sb" : {"cooldown" : spam_cooldown},
		"u#se" : {"cooldown" : 3}, #Avoid ET spam!
		"b#br" : {"cooldown" : spam_cooldown}, #Avoid ET spam!
	}

	handlers = {
		"b#gb"		: "handleGetBuddies",
		"b#br"		: "handleBuddyRequest",
		"b#ba"		: "handleBuddyAdd",
		"b#rb"		: "handleBuddyRemove",
		"b#bf"		: "handleBuddyFind",

		"n#gn"		: "handleGetIgnore",

		"j#jr"		: "handleJoinRoom",
		"j#js"		: "handleJoinServer",

		"i#gi"		: "handleGetInventory",

		"l#mst"		: "handleLoadMst",
		"l#mg"		: "handleLoadMg",

		"m#sm"		: "handleSendMessage",

		"u#glr"		: "handleGetLastRevision",
		"u#h"		: "handleHeartbeat",
		"u#sp"		: "handleSendPosition",
		"u#gp"		: "handleGetPlayer",
		"u#se"		: "handleSendEmote",
		"u#sf"		: "handleSendFrame",
		"u#ss"		: "handleSendSafeMessage",
		"u#sq"		: "handleSendQuickMessage",
		"u#sa"		: "handleSendAction",
		"u#sb"		: "handleSnowBall",

		"s#upc"		: "handleUpdateColor",
		"s#uph"		: "handleUpdateHead",
		"s#upf"		: "handleUpdateFace",
		"s#upn"		: "handleUpdateNeck",
		"s#upb"		: "handleUpdateBody",
		"s#upa"		: "handleUpdateHand",
		"s#upe"		: "handleUpdateFeet",
		"s#upl"		: "handleUpdatePin",
		"s#upp"		: "handleUpdateBackground",

		#Unused Handlers
		"f#epfgf" 	: "handlePass",
		"f#epfgr"	: "handlePass",
		"f#epfga"	: "handlePass",
		"p#pgu"		: "handlePass",
		"i#qpa"		: "handlePass",
	}

	def __init__(self, o2, client):
		self.client = client
		self.o2 = o2
		self.commands = commands.commands(o2, client)
		self.history = {}

		for handler in self.throttle:
			self.history[handler] = 0

		print(self.history)

	async def handleXt(self, data):
		#try:
		og_data = data
		data = data.split("%")
		handler = data[3]
		toSend = []

		for i in range(4, len(data)):
			if(len(data[i]) >= 1):
				toSend.append(data[i])

		if(handler in self.handlers.keys()):
			if(handler not in self.throttle.keys()):
				callHandler = getattr(self, self.handlers[handler])
				await callHandler(toSend)
				return True

			else:
				current_time = await self.o2.getCurrentTimeSeconds()
				old_time = self.history[handler]
				cooldown = self.throttle[handler]['cooldown']

				if cooldown is not -1:
					if((current_time - old_time) >= cooldown):
						callHandler = getattr(self, self.handlers[handler])
						await callHandler(toSend)
						self.history[handler] = current_time
						return True
					
				print("Rate limited")
				return True
		else:
			self.log("A designated handler could not be found. Packet: {%s}" % (og_data))
			print()

		#except Exception as e:
		#	self.log("A designated handler could not be found. Packet: {%s}. Additional Error Information: {%s}" % (og_data, str(e)))
		#	print()
		#	return False

	def log(self, message):
		message = self.client.player['username'] + "->" + message
		self.o2.logging.log("client", ("game", self.client.ip, "handlers", str(message)))

	async def handlePass(self, data):
		return

	async def handleJoinRoom(self, data):
		room_id = data[1]
		x = data[2]
		y = data[3]
		await self.client.joinRoom(room_id, x, y)

	async def handleJoinServer(self, data):
		isModerator = 0
		age = 6969
		minsPlayed = 420
		memDays = 32444444

		await self.client.sendXt("js", "-1", "1", "1", isModerator)
		await self.client.sendXt("lp", "-1", await self.client.getPlayerString(), await self.client.getCoins(), r"0%1440%1333337%" + str(age) + r"%0%" + str(minsPlayed) + "%" + str(memDays) + "%7")
		await self.client.sendXt("gps", "-1", "")
		await self.client.joinRoom(100)

	async def handleGetInventory(self, data):
		await self.client.sendXt("gi", "1", "1", await self.client.getInventory())

	async def handleGetBuddies(self, data):
		await self.client.sendXt("gb", "-1", await self.client.getBuddies())

	async def handleBuddyRequest(self, data):
		try:
			room_int = data[0]
			buddy_id = int(data[1])

			if buddy_id in self.o2.players:
				#"br", $client->intRoomID, $client->ID, getName($client->ID)), $id)
				#%xt%br%2%101%T Zog%
				await self.o2.players[buddy_id].sendXt("br", room_int, self.client.player['id'], self.client.player['username'])

		except (ValueError, IndexError):
			return

	"""
	INFO:Houdini:Received XT data:	%xt%s%b#ba%2%101%
	INFO:Houdini:Outgoing data: 	%xt%ba%2%105%Graph%
	"""
	async def handleBuddyAdd(self, data):
		try:
			room_int = data[0]
			request_id = int(data[1])

			if request_id in self.o2.players:
				await self.o2.players[request_id].sendXt("ba", room_int, self.client.player['id'], self.client.player['username'])
				await self.client.addBuddy(request_id)

		except (ValueError, IndexError):
			return

	"""
	INFO:Houdini:Received XT data: %xt%s%b#rb%16%101%
	INFO:Houdini:Outgoing data: %xt%rb%2%105%
	"""

	async def handleBuddyRemove(self, data):
		try:
			room_int = data[0]
			remove_id = int(data[1])

			if remove_id in self.o2.players:
				await self.o2.players[remove_id].sendXt("rb", room_int, self.client.player['id'])
				await self.client.removeBuddy(remove_id)

		except (ValueError, IndexError):
			return

	"""
	INFO:Houdini:Received XT data: %xt%s%b#bf%2%101%
	INFO:Houdini:Outgoing data: %xt%bf%2%810%
	"""

	async def handleBuddyFind(self, data):
		await self.client.getBuddies(refresh=True)

		try:
			room_int = data[0]
			buddy_id = int(data[1])
			buddies = self.client.player['buddies']
			my_buddy_ids = []

			for buddy in buddies:
				my_buddy_ids.append(int(buddy.split("|")[0]))

			if (buddy_id in self.o2.players) and (buddy_id in my_buddy_ids):
				buddy_room = self.o2.players[buddy_id].player['room']
				await self.client.sendXt("bf", room_int, buddy_room)

		except (ValueError, IndexError):
			return

	async def handleGetIgnore(self, data):
		#await self.client.sendXt("gb", "-1", "")
		print("Kottonmouth")
		return

	async def handleLoadMst(self, data):
		await self.client.sendXt("mst", "-1", "", "")

	async def handleLoadMg(self, data):
		await self.client.sendXt("mg", "")

	async def handleGetLastRevision(self, data):
		await self.client.sendXt("glr", "1337", "1337")

	async def handleHeartbeat(self, data):
		await self.client.sendXt("h", "-1")

	async def handleSendPosition(self, data):
		x = data[1] or 0
		y = data[2] or 0

		self.client.player['string']['x'] = x
		self.client.player['string']['y'] = y

		await self.client.sendRoomXt("sp", self.o2.roomInts[self.client.player['room']], self.client.player['id'], x, y)

	#{%xt%s%u#gp%23%3%}
	#INFO:Houdini:Received XT data: %xt%s%u#gp%23%105%
	#INFO:Houdini:Outgoing data: %xt%gp%23%105|Graph|1|0xff0000|415|0|0|218|220|351|550|901%

	async def handleGetPlayer(self, data):
		try:
			room_int = data[0]
			buddy_id = int(data[1])

			if buddy_id in self.o2.players:
				await self.client.sendXt("gp", room_int, await self.o2.players[buddy_id].getPlayerString())

		except (ValueError, IndexError):
			return

	async def handleSendEmote(self, data):
		room_int = data[0]
		emote_id = data[1]

		await self.client.sendRoomXt("se", room_int, self.client.player['id'], emote_id)

	async def handleSendFrame(self, data):
		room_int = data[0]
		frame_id = data[1]
		self.client.player['frame'] = frame_id

		await self.client.sendRoomXt("sf", room_int, self.client.player['id'], frame_id)

	async def handleSendSafeMessage(self, data):
		room_int = data[0]
		message_id = data[1]

		await self.client.sendRoomXt("ss", room_int, self.client.player['id'], message_id)

	async def handleSendQuickMessage(self, data):
		room_int = data[0]
		message_id = data[1]

		await self.client.sendRoomXt("sq", room_int, self.client.player['id'], message_id)

	async def handleSendAction(self, data):
		room_int = data[0]
		action_id = data[1]

		await self.client.sendRoomXt("sa", room_int, self.client.player['id'], action_id)

	async def handleSnowBall(self, data):
		room_int = data[0]
		x = data[1]
		y = data[2]

		await self.client.sendRoomXt("sb", room_int, self.client.player['id'], x, y)

	async def handleSendMessage(self, data):
		room_int = data[0]
		message = data[2]

		if(message[0] == self.o2.config['commands']['char']):
			await self.commands.handleCommand(message)

		await self.client.sendRoomXt("sm", room_int, self.client.player['id'], message)

	async def handleUpdateColor(self, data):
		room_int = data[0]
		item_id = data[1]

		self.client.player['string']['color'] = int(item_id)
		await self.client.sendRoomXt("upc", room_int, self.client.player['id'], item_id)

	async def handleUpdateHead(self, data):
		room_int = data[0]
		item_id = data[1]

		self.client.player['string']['head'] = int(item_id)
		await self.client.sendRoomXt("uph", room_int, self.client.player['id'], item_id)

	async def handleUpdateFace(self, data):
		room_int = data[0]
		item_id = data[1]

		self.client.player['string']['face'] = int(item_id)
		await self.client.sendRoomXt("upf", room_int, self.client.player['id'], item_id)

	async def handleUpdateNeck(self, data):
		room_int = data[0]
		item_id = data[1]

		self.client.player['string']['neck'] = int(item_id)
		await self.client.sendRoomXt("upn", room_int, self.client.player['id'], item_id)

	async def handleUpdateBody(self, data):
		room_int = data[0]
		item_id = data[1]

		self.client.player['string']['body'] = int(item_id)
		await self.client.sendRoomXt("upb", room_int, self.client.player['id'], item_id)

	async def handleUpdateHand(self, data):
		room_int = data[0]
		item_id = data[1]

		self.client.player['string']['hand'] = int(item_id)
		await self.client.sendRoomXt("upa", room_int, self.client.player['id'], item_id)

	async def handleUpdateFeet(self, data):
		room_int = data[0]
		item_id = data[1]

		self.client.player['string']['feet'] = int(item_id)
		await self.client.sendRoomXt("upe", room_int, self.client.player['id'], item_id)

	async def handleUpdatePin(self, data):
		room_int = data[0]
		item_id = data[1]

		self.client.player['string']['pin'] = int(item_id)
		await self.client.sendRoomXt("upl", room_int, self.client.player['id'], item_id)

	async def handleUpdateBackground(self, data):
		room_int = data[0]
		item_id = data[1]

		self.client.player['string']['background'] = int(item_id)
		await self.client.sendRoomXt("upp", room_int, self.client.player['id'], item_id)