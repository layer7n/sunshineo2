class logger:

	def __init__(self):
		self.config = {}
		self.logBoot("logger", "Module Loaded")
		return

	def log(self, type, message):
		if(type is not "client"):
			print("[%s]: %s" % (type.upper(), message))
		else:
			if(not self.config['dev_mode']):
				return

			subType = message[0]
			cliAddr = message[1][0] + ":" + str(message[1][1])
			subHandle = message[2]
			sep = ""

			if(len(subHandle) <= 12):
				sep += "\t"

			data = message[3]
			if((not self.config['detailed_logging']) and (len(data) >= 80)):
				data = data[0:80] + "[...]"

			print("[%s][%s::%s]\t[%s]=>%s\t{%s}" % (type.upper(), subType.upper(), cliAddr, subHandle.upper(), sep, data))

	def logBoot(self, type, message):
		print(" =>[%s]: %s" % (type.upper(), message))
