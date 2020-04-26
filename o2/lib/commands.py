class commands:

	#TO-DO Command Cooldowns

	throttle = {
		"ai"	: {"cooldown" : 1}, #can only do once per second
	}

	commands = {
		"ai"	: "handleAddItem",
	}

	def __init__(self, o2, client):
		self.o2 = o2
		self.client = client

	async def handleCommand(self, command):
		command = command[1:]
		command = command.split(" ")
		command = {
			"index" 	: command[0],
			"contents" 	: command[1:], 
		}

		if(command['index'] in self.commands.keys()):
			callHandler = getattr(self, self.commands[command['index']])
			await callHandler(command['contents'])
			return True

		print("Command not found.")
		return False

	async def handleAddItem(self, data):
		await self.client.addItem(data[0])
		return