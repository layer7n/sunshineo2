class bootscreen:

	def __init__(self):
		return

	def showBootScreen(self, type):
		print()
		print()
		print(r"                     __   _               ___ ")
		print(r"  ___ __ _____  ___ / /  (_)__  ___ ___  |_  |")
		print(r" (_-</ // / _ \(_-</ _ \/ / _ \/ -_) _ \/ __/ ")
		print(r"/___/\_,_/_//_/___/_//_/_/_//_/\__/\___/____/ ")
                                              

		print("   Written by ^r ")
		print("        A Powerful Asynchronous AS2 Emulator...")
		print()
		print()
		print("+-------[Initializing Components]-------+")
		print(" =>[MODE]: %s Server" % (type.title()))
		print("+---------------------------------------+")
												   
	def closeBootScreen(self):
		print("+---------------------------------------+")
		print()