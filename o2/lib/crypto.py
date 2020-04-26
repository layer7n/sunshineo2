import random
import hashlib

class crypto:

	def __init__(self, length=12):
		self.length = length
		return

	async def createRandomKey(self):
		key = ""
		bank = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456789"

		for i in range(self.length):
			key += random.choice(bank)

		return(key)

	async def formatHash(self, password, rndk):
		password = hashlib.md5((((password[16:32] + password[0:16]).upper()) + rndk + "Y(02.>'H}t\":E1").encode('utf-8')).hexdigest()
		return(password[16:32] + password[0:16])

	async def createLoginKey(self, rndk):
		return hashlib.md5(rndk.encode("utf-8")).hexdigest()

	async def createLoginHash(self, login_key, rndk):
		hash = login_key + rndk
		hash = hashlib.md5(hash.encode("utf-8")).hexdigest()
		return(hash[16:32] + hash[0:16] + login_key)