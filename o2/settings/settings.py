class config:

	def __init__(self, logger):
		self.logger = logger
		self.config = {
			"logging" : {
				"dev_mode" : True,
				"detailed_logging" : True,
			},
			"login" : {
				"host" : "127.0.0.1",
				"port" : 6112,
			},
			"game" : {
				"host" : "127.0.0.1",
				"port" : 9875,
			},
			"db" : {
				"host" : "localhost",
				"user" : "postgres",
				"pass" : "mac", 
				"db_name" : "o2", 
			},
			"commands" : {
				"char" : "!",
			},
		}

		self.logger.logBoot("config", "Module Loaded")
		return