import json

class buildCrumbs:

	def __init__(self):
		return

	async def build(self, type):
		crumb = {}

		if(type == "room_ints"):
			return await self.buildRoomInts()

		with open("o2/crumbs/" + type + ".json") as f:
			j = json.loads(f.read())

		for i in j:
			crumb[int(i)] = list()

		return(crumb)

	async def buildRoomInts(self):
		room_ints = {}

		with open("o2/crumbs/rooms.json") as f:
			rooms = json.loads(f.read())

		for i in rooms:
			room_ints[int(i)] = rooms[i]['internal_id']

		return(room_ints)